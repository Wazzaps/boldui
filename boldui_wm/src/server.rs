use crate::utils::SerdeSender;
use anyhow::Context;
use boldui_protocol::serde::de::DeserializeOwned;
use boldui_protocol::{
    bincode, A2RMessage, R2AMessage, R2AOpen, R2AUpdate, WmHello, WmHelloAction, WM_REQ_MAGIC,
};
use std::collections::HashMap;
use std::io::{ErrorKind, IoSliceMut};
use std::mem::size_of;
use std::ops::DerefMut;
use std::os::fd::{FromRawFd, IntoRawFd, OwnedFd};
use std::sync::Arc;
use tokio::fs::File;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::sync::mpsc::{Receiver, Sender};
use tokio::sync::{mpsc, Mutex, Notify};
use tokio_seqpacket::ancillary::OwnedAncillaryMessage;
use tokio_seqpacket::{UnixSeqpacket, UnixSeqpacketListener};
use tracing::{debug, error, info, trace};

pub struct MainLoop {
    renderer_kill_flag: Notify,
    renderer_mutex: Mutex<RendererState>,
    ctrl_sock_clients: Mutex<Vec<UnixSeqpacket>>,
}

#[derive(Debug, Default)]
struct RendererState {
    pub apps: HashMap<usize, RendererAppState>,
    pub app2renderer_recv: Option<Receiver<(usize, App2RendererMsg)>>,
}

#[derive(Debug)]
struct RendererAppState {
    pub renderer2app_send: Sender<Renderer2AppMsg>,
}

impl MainLoop {
    pub fn new() -> anyhow::Result<Self> {
        Ok(MainLoop {
            renderer_kill_flag: Notify::new(),
            renderer_mutex: Mutex::new(RendererState::default()),
            ctrl_sock_clients: Mutex::new(Vec::new()),
        })
    }

    pub fn run(self, sock_addr: &str) -> anyhow::Result<()> {
        tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .build()
            .unwrap()
            .block_on(self.run_inner(sock_addr))
    }

    async fn handle_app(
        self: Arc<Self>,
        app_id: usize,
        mut app_stdin: File,
        mut app_stdout: File,
        renderer2app_send: Sender<Renderer2AppMsg>,
        mut renderer2app_recv: Receiver<Renderer2AppMsg>,
        app2renderer_send: Sender<(usize, App2RendererMsg)>,
    ) -> anyhow::Result<()> {
        Self::app_send_hello(&mut app_stdin, &mut app_stdout)
            .await
            .context("Failed while sending hello message")?;

        info!("new app id {}", app_id);
        app2renderer_send
            .send((app_id, App2RendererMsg::NewApp { renderer2app_send }))
            .await
            .context("Failed while notifying renderer task of new app")?;

        let mut msg_buf = Vec::new();
        loop {
            tokio::select! {
                msg_len = app_stdout.read_u32_le() => {
                    // TODO: buffered reader?
                    let msg_len = match msg_len {
                        Ok(len) => len,
                        Err(e) if e.kind() == ErrorKind::UnexpectedEof => {
                            debug!("app #{} connection closed, bye!", app_id);
                            return Ok(());
                        }
                        Err(e) => Err(e)?,
                    };

                    trace!("reading msg of size {msg_len}");
                    msg_buf.resize(msg_len as usize, 0);
                    app_stdout.read_exact(&mut msg_buf).await?;
                    let msg = bincode::deserialize::<A2RMessage>(&msg_buf)?;

                    trace!("R2A: {:#?}", &msg);
                    match msg {
                        // TODO: map ids
                        A2RMessage::Update(u) => app2renderer_send.send((app_id, App2RendererMsg::A2RMessage(A2RMessage::Update(u)))).await?,
                        A2RMessage::Error(e) => todo!("app error: {:?}", e),
                        A2RMessage::CompressedUpdate(u) => todo!("compressed update: {:?}", u),
                    }
                }
                r2a = renderer2app_recv.recv() => {
                    let r2a_msg = r2a.unwrap();
                    Self::app_handle_r2a_msg(&mut app_stdin, r2a_msg).await?;
                }
            }
        }
    }

    async fn app_handle_r2a_msg(
        app_stdin: &mut File,
        r2a_msg: Renderer2AppMsg,
    ) -> anyhow::Result<()> {
        match r2a_msg {
            Renderer2AppMsg::R2AMessage(inner) => {
                // debug!("R2A: {:?}", &R2AMessage::Open(o.clone()));
                app_stdin.send(&inner).await?;
                app_stdin.flush().await?;
            }
        };
        Ok(())
    }

    async fn handle_renderer(
        self: Arc<Self>,
        mut renderer_stdin: File,
        mut renderer_stdout: File,
        renderer_state: &mut RendererState,
    ) -> anyhow::Result<()> {
        Self::renderer_recv_hello(&mut renderer_stdin, &mut renderer_stdout).await?;

        // TODO: re-open all current windows

        let mut msg_buf = Vec::new();
        loop {
            tokio::select! {
                msg_len = renderer_stdin.read_u32_le() => {
                    // TODO: buffered reader?
                    let msg_len = match msg_len {
                        Ok(len) => len,
                        // TODO: test if this works
                        Err(e) if e.kind() == ErrorKind::UnexpectedEof => {
                            debug!("renderer connection closed, bye!");
                            return Ok(());
                        }
                        Err(e) => Err(e)?,
                    };
                    trace!("reading msg of size {msg_len}");
                    msg_buf.resize(msg_len as usize, 0);
                    renderer_stdin.read_exact(&mut msg_buf).await?;
                    let msg = bincode::deserialize::<R2AMessage>(&msg_buf)?;

                    trace!("R2A: {:#?}", &msg);
                    match msg {
                        R2AMessage::Update(R2AUpdate { replies }) => {
                            trace!("Replies: {:?}", &replies);
                            // TODO: append prefix to paths, only send replies to relevant app
                            for app in renderer_state.apps.values() {
                                app.renderer2app_send
                                    .send(Renderer2AppMsg::R2AMessage(R2AMessage::Update(R2AUpdate {
                                        replies: replies.clone(),
                                    })))
                                    .await?;
                            }
                        }
                        R2AMessage::Open(R2AOpen { path }) => {
                            if path.is_empty() {
                                info!("Open(\"/\") from renderer, opening all windows");
                                for app in renderer_state.apps.values() {
                                    app.renderer2app_send
                                        .send(Renderer2AppMsg::R2AMessage(R2AMessage::Open(R2AOpen {
                                            path: path.clone(),
                                        })))
                                        .await?;
                                }
                            } else {
                                info!("Open({:?}) from renderer, ignoring", &path);

                            }
                        }
                        R2AMessage::Error(err) => {
                            error!("Renderer error: {err:?}");
                        }
                    }
                }

                a2r = renderer_state.app2renderer_recv.as_mut().unwrap().recv() => {
                    let (app_id, a2r_msg) = a2r.unwrap();
                    Self::renderer_handle_a2r_msg(renderer_state, &mut renderer_stdout, app_id, a2r_msg).await?;
                }
            }
        }
    }

    async fn renderer_handle_a2r_msg(
        renderer_state: &mut RendererState,
        renderer_stdout: &mut File,
        app_id: usize,
        a2r_msg: App2RendererMsg,
    ) -> anyhow::Result<()> {
        match a2r_msg {
            App2RendererMsg::NewApp { renderer2app_send } => {
                renderer_state
                    .apps
                    .insert(app_id, RendererAppState { renderer2app_send });

                // Open initial window
                renderer_state.apps[&app_id]
                    .renderer2app_send
                    .send(Renderer2AppMsg::R2AMessage(R2AMessage::Open(R2AOpen {
                        path: "".to_string(),
                    })))
                    .await?;
            }
            App2RendererMsg::A2RMessage(inner) => {
                // debug!("A2R: {:?}", &inner);
                renderer_stdout.send(&inner).await?;
                renderer_stdout.flush().await?;
            }
        };
        Ok(())
    }

    #[allow(clippy::absurd_extreme_comparisons)]
    async fn renderer_recv_hello(
        mut renderer_stdin: &mut File,
        renderer_stdout: &mut File,
    ) -> anyhow::Result<()> {
        // Get hello
        {
            debug!("reading hello");
            let mut magic = [0u8; boldui_protocol::R2A_MAGIC.len()];
            renderer_stdin.read_exact(&mut magic).await.unwrap();
            assert_eq!(&magic, boldui_protocol::R2A_MAGIC, "Missing magic");

            let hello =
                bincode_deserialize::<boldui_protocol::R2AHello>(&mut renderer_stdin).await?;
            assert!(
                boldui_protocol::LATEST_MAJOR_VER <= hello.max_protocol_major_version
                    && (boldui_protocol::LATEST_MAJOR_VER > hello.min_protocol_major_version
                        || (boldui_protocol::LATEST_MAJOR_VER == hello.min_protocol_major_version
                            && boldui_protocol::LATEST_MINOR_VER
                                >= hello.min_protocol_minor_version)),
                "Incompatible version"
            );
            assert_eq!(
                hello.extra_len, 0,
                "This protocol version specifies no extra data"
            );
        }

        // Reply with A2RHelloResponse
        {
            debug!("sending hello response");
            renderer_stdout
                .write_all(boldui_protocol::A2R_MAGIC)
                .await?;
            renderer_stdout
                .write_all(&bincode::serialize(&boldui_protocol::A2RHelloResponse {
                    protocol_major_version: boldui_protocol::LATEST_MAJOR_VER,
                    protocol_minor_version: boldui_protocol::LATEST_MINOR_VER,
                    extra_len: 0,
                    error: None,
                    // error: Some(boldui_protocol::CommonError {
                    //     code: 123,
                    //     text: "Foo".to_string(),
                    // }),
                })?)
                .await?;
            renderer_stdout.flush().await?;
            debug!("connected!");
        };
        Ok(())
    }

    async fn app_send_hello(app_stdin: &mut File, app_stdout: &mut File) -> anyhow::Result<()> {
        // Send hello
        {
            debug!("sending hello");

            app_stdin.write_all(boldui_protocol::R2A_MAGIC).await?;
            app_stdin
                .write_all(&bincode::serialize(&boldui_protocol::R2AHello {
                    min_protocol_major_version: boldui_protocol::LATEST_MAJOR_VER,
                    min_protocol_minor_version: boldui_protocol::LATEST_MINOR_VER,
                    max_protocol_major_version: boldui_protocol::LATEST_MAJOR_VER,
                    extra_len: 0, // No extra data
                })?)
                .await?;
            app_stdin.flush().await?;
        }

        // Get hello response
        {
            debug!("reading hello response");
            let mut magic = [0u8; boldui_protocol::A2R_MAGIC.len()];
            app_stdout.read_exact(&mut magic).await?;
            assert_eq!(&magic, boldui_protocol::A2R_MAGIC, "Missing magic");

            let hello_res =
                bincode_deserialize::<boldui_protocol::A2RHelloResponse>(app_stdout).await?;

            assert_eq!(
                (
                    hello_res.protocol_major_version,
                    hello_res.protocol_minor_version
                ),
                (
                    boldui_protocol::LATEST_MAJOR_VER,
                    boldui_protocol::LATEST_MINOR_VER
                ),
                "Incompatible version"
            );
            assert_eq!(
                hello_res.extra_len, 0,
                "This protocol version specifies no extra data"
            );

            if let Some(err) = hello_res.error {
                panic!("An error has occurred: code {}: {}", err.code, err.text);
            }
            debug!("connected!");
        };
        Ok(())
    }

    async fn run_inner(self, sock_addr: &str) -> anyhow::Result<()> {
        let (app_send, mut app_recv) = mpsc::channel(8);
        let (renderer_send, mut renderer_recv) = mpsc::channel(8);
        let (app2renderer_send, app2renderer_recv) = mpsc::channel(8);
        self.renderer_mutex.lock().await.app2renderer_recv = Some(app2renderer_recv);

        let _this = Arc::new(self);

        let this = _this.clone();
        let mut ctrl_sock = UnixSeqpacketListener::bind_with_backlog(sock_addr, 4)?;
        let control_handler = tokio::spawn(async move {
            loop {
                let client = ctrl_sock.accept().await.unwrap();
                let this = this.clone();
                let app_send = app_send.clone();
                let renderer_send = renderer_send.clone();
                tokio::spawn(async move {
                    let mut buf = [0u8; WM_REQ_MAGIC.len() + size_of::<WmHello>()];
                    let fds = read_buf_with_fds(&client, &mut buf).await.unwrap();
                    assert!(buf.starts_with(WM_REQ_MAGIC));

                    let hello = unsafe {
                        (buf[WM_REQ_MAGIC.len()..].as_ptr() as *const WmHello)
                            .as_ref()
                            .unwrap_unchecked()
                    };

                    match hello.action {
                        WmHelloAction::ConnectApp => {
                            info!("app fds: {:?}", fds);
                            let (input, output) = fds_into_two_files(fds);
                            app_send.send((input, output)).await.unwrap();
                        }
                        WmHelloAction::AttachRenderer => {
                            info!("renderer fds: {:?}", fds);
                            let (input, output) = fds_into_two_files(fds);
                            renderer_send.send((input, output)).await.unwrap();
                        }
                    }

                    this.ctrl_sock_clients.lock().await.push(client);
                });
            }
        });

        let this = _this.clone();
        let app_handler = tokio::spawn(async move {
            let mut app_counter = 0usize;
            loop {
                let app2renderer_send = app2renderer_send.clone();
                let app_id = app_counter;
                app_counter += 1;
                let (input, output) = app_recv.recv().await.unwrap();
                info!("Got app");
                let this = this.clone();
                // TODO: tweak queue bound?
                let (renderer2app_send, renderer2app_recv) = mpsc::channel(8);

                tokio::spawn(async move {
                    this.handle_app(
                        app_id,
                        input,
                        output,
                        renderer2app_send,
                        renderer2app_recv,
                        app2renderer_send,
                    )
                    .await
                    .unwrap_or_else(|e| error!("App handler error: {:?}", e));
                });
            }
        });

        let this = _this.clone();
        let renderer_handler = tokio::spawn(async move {
            let mut is_first = true;
            loop {
                let (input, output) = renderer_recv.recv().await.unwrap();
                info!("Got renderer");
                let this = this.clone();

                if !is_first {
                    this.renderer_kill_flag.notify_one();
                }
                is_first = false;

                tokio::spawn(async move {
                    let this2 = this.clone();
                    let mut state = this2.renderer_mutex.lock().await;
                    let handler = this.handle_renderer(input, output, state.deref_mut());
                    tokio::select! {
                        _ = this2.renderer_kill_flag.notified() => {
                            debug!("New renderer coming in, killing old one");
                        }
                        _ = handler => {}
                    }
                });
            }
        });

        renderer_handler.await?;
        app_handler.await?;
        control_handler.await?;
        Ok(())
    }
}

async fn bincode_deserialize<T: DeserializeOwned>(file: &mut File) -> anyhow::Result<T> {
    let mut buf = Vec::new();
    loop {
        let prev_len = buf.len();
        buf.resize(prev_len + 1024, 0);
        let bytes_read = file.read(&mut buf[prev_len..]).await?;
        buf.truncate(prev_len + bytes_read);
        if let Ok(data) = bincode::deserialize(&buf) {
            return Ok(data);
        }
    }
}

async fn read_buf_with_fds(client: &UnixSeqpacket, buf: &mut [u8]) -> anyhow::Result<Vec<OwnedFd>> {
    let mut sa_buf = Vec::new();
    sa_buf.resize(256, 0u8);

    let (buf_len, anc_msg_reader) = client
        .recv_vectored_with_ancillary(&mut [IoSliceMut::new(buf)], &mut sa_buf)
        .await
        .unwrap();

    let mut fds = vec![];
    for msg in anc_msg_reader.into_messages() {
        match msg {
            OwnedAncillaryMessage::FileDescriptors(f) => {
                fds.extend(f);
            }
            _ => panic!("got unexpected ancillary data"),
        }
    }

    if buf_len != buf.len() {
        anyhow::bail!("Failed to read all data");
    }

    Ok(fds)
}

fn fds_into_two_files(fds: Vec<OwnedFd>) -> (File, File) {
    assert_eq!(fds.len(), 2, "Expected exactly two fds (stdin, stdout)");
    let [input, output]: [File; 2] = fds
        .into_iter()
        .map(|fd| unsafe { File::from_raw_fd(fd.into_raw_fd()) })
        .collect::<Vec<_>>()
        .try_into()
        .unwrap();

    (input, output)
}

#[derive(Debug)]
enum Renderer2AppMsg {
    R2AMessage(R2AMessage),
}

#[derive(Debug)]
enum App2RendererMsg {
    NewApp {
        renderer2app_send: Sender<Renderer2AppMsg>,
    },
    A2RMessage(A2RMessage),
}
