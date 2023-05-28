use boldui_protocol::serde::de::DeserializeOwned;
use boldui_protocol::{bincode, WmHello, WmHelloAction, WM_REQ_MAGIC};
use std::io::IoSliceMut;
use std::mem::size_of;
use std::ops::DerefMut;
use std::os::fd::{FromRawFd, IntoRawFd, OwnedFd};
use std::sync::Arc;
use tokio::fs::File;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::sync::{mpsc, Mutex, Notify};
use tokio_seqpacket::ancillary::OwnedAncillaryMessage;
use tokio_seqpacket::{UnixSeqpacket, UnixSeqpacketListener};
use tracing::{debug, info};

pub struct MainLoop {
    renderer_kill_flag: Notify,
    renderer_mutex: Mutex<RendererState>,
    ctrl_sock_clients: Mutex<Vec<UnixSeqpacket>>,
}

#[derive(Debug, Default)]
struct RendererState {}

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
        mut app_stdin: File,
        mut app_stdout: File,
    ) -> anyhow::Result<()> {
        Self::send_hello(&mut app_stdin, &mut app_stdout).await?;

        Ok(())
    }

    #[allow(clippy::absurd_extreme_comparisons)]
    async fn handle_renderer(
        self: Arc<Self>,
        mut renderer_stdin: File,
        mut renderer_stdout: File,
        _renderer_state: &mut RendererState,
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
        }

        Ok(())
    }

    async fn send_hello(app_stdin: &mut File, app_stdout: &mut File) -> anyhow::Result<()> {
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
            loop {
                let (input, output) = app_recv.recv().await.unwrap();
                info!("Got app");
                let this = this.clone();

                tokio::spawn(async move {
                    this.handle_app(input, output).await.unwrap();
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
