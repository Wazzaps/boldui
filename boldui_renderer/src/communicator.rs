use crate::dmabuf::{ExternalApp, TextureStorageMetadata};
use crate::state_machine::WindowId;
use crate::util::{any_as_u8_slice_mut, u8_slice_as_any};
use crate::{EventLoopProxy, SerdeSender};
use boldui_protocol::{bincode, A2RMessage, A2RUpdate, EA2RMessage, R2AReply, R2AUpdate, SceneId};
use byteorder::{ReadBytesExt, LE};
use crossbeam::channel::{Receiver, Sender};
use eventfd::EventFD;
use nix::sys::select::{select, FdSet};
use skia_safe::gpu::BackendTexture;
use std::cmp::min;
use std::collections::HashMap;
use std::fs::File;
use std::io::{IoSliceMut, Read, Write};
use std::os::fd::{FromRawFd, OwnedFd, RawFd};
use std::os::unix::io::AsRawFd;
use std::os::unix::net::{AncillaryData, SocketAncillary, UnixStream};
use std::time::Instant;
use tracing::{debug, error, info, trace};

#[derive(Debug)]
pub(crate) enum ToStateMachine {
    Quit,
    Redraw {
        window_id: WindowId,
    },
    AllocWindow(SceneId),
    SleepUntil(Instant),
    Click {
        window_id: WindowId,
        x: f64,
        y: f64,
        button: u8,
    },
    Update(A2RUpdate),
    SimulatorTick {
        from_update: bool,
    },
    MountExternalWidget {
        scene_id: SceneId,
        texture_metadata: TextureStorageMetadata,
        texture_fd: OwnedFd,
    },
}

pub(crate) enum FromStateMachine {
    Quit,
    Reply(R2AReply),
    RequestExternalWidget { scene_id: SceneId, uri: String },
}

pub(crate) struct CommChannelRecv {
    pub recv: Receiver<FromStateMachine>,
    pub notify_recv: EventFD,
}

pub(crate) struct CommChannelSend {
    pub send: Sender<FromStateMachine>,
    pub notify_send: EventFD,
}

pub(crate) struct ConnectionInitiator {
    pub app_stdin: File,
    pub app_stdout: File,
}

pub(crate) struct Communicator {
    pub app_stdin: File,
    pub app_stdout: File,
    pub external_apps: HashMap<String, ExternalApp>,
    pub event_loop_proxy: Box<dyn EventLoopProxy + Send>,
    pub comm_channel_recv: CommChannelRecv,
}

impl ConnectionInitiator {
    pub fn connect(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // Send hello
        {
            debug!("sending hello");

            self.app_stdin.write_all(boldui_protocol::R2A_MAGIC)?;
            self.app_stdin
                .write_all(&bincode::serialize(&boldui_protocol::R2AHello {
                    min_protocol_major_version: boldui_protocol::LATEST_MAJOR_VER,
                    min_protocol_minor_version: boldui_protocol::LATEST_MINOR_VER,
                    max_protocol_major_version: boldui_protocol::LATEST_MAJOR_VER,
                    extra_len: 0, // No extra data
                })?)?;
            self.app_stdin.flush()?;
        }

        // Get hello response
        {
            debug!("reading hello response");
            let mut magic = [0u8; boldui_protocol::A2R_MAGIC.len()];
            self.app_stdout.read_exact(&mut magic).unwrap();
            assert_eq!(&magic, boldui_protocol::A2R_MAGIC, "Missing magic");

            let hello_res = bincode::deserialize_from::<_, boldui_protocol::A2RHelloResponse>(
                &mut self.app_stdout,
            )?;

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
        }
        Ok(())
    }

    pub fn send_open(&mut self, path: String) -> Result<(), Box<dyn std::error::Error>> {
        debug!("sending R2AOpen");
        self.app_stdin.send(&boldui_protocol::R2AMessage::Open(
            boldui_protocol::R2AOpen { path },
        ))?;

        Ok(())
    }

    pub fn into_communicator(
        self,
        event_loop_proxy: Box<dyn EventLoopProxy + Send>,
        comm_channel_recv: CommChannelRecv,
    ) -> Communicator {
        Communicator {
            app_stdin: self.app_stdin,
            app_stdout: self.app_stdout,
            event_loop_proxy,
            comm_channel_recv,
            external_apps: HashMap::new(),
        }
    }
}

fn read_fds(sock: &mut UnixStream) -> Vec<OwnedFd> {
    let mut fds = vec![];
    let mut sa_buf = Vec::new();
    sa_buf.resize(256, 0u8);
    let mut sa = SocketAncillary::new(sa_buf.as_mut_slice());
    sock.recv_vectored_with_ancillary(&mut [], &mut sa).unwrap();
    for msg in sa.messages() {
        match msg.unwrap() {
            AncillaryData::ScmRights(mut r) => {
                for fd in r {
                    fds.push(unsafe { OwnedFd::from_raw_fd(fd) });
                }
            }
            AncillaryData::ScmCredentials(_) => {
                panic!("got unexpected credentials");
            }
        }
    }
    fds
}

fn read_with_fds(sock: &mut UnixStream, size: usize) -> std::io::Result<(Vec<u8>, Vec<OwnedFd>)> {
    let mut data = vec![];
    let mut fds = vec![];
    let mut sa_buf = Vec::new();
    sa_buf.resize(256, 0u8);
    let mut curr_size = 0;
    while curr_size < size {
        data.resize(min(curr_size + (32 * 1024), size), 0);

        let mut sa = SocketAncillary::new(sa_buf.as_mut_slice());
        sock.recv_vectored_with_ancillary(&mut [IoSliceMut::new(&mut data[curr_size..])], &mut sa)?;

        for msg in sa.messages() {
            match msg.unwrap() {
                AncillaryData::ScmRights(mut r) => {
                    for fd in r {
                        fds.push(unsafe { OwnedFd::from_raw_fd(fd) });
                    }
                }
                AncillaryData::ScmCredentials(_) => {
                    panic!("got unexpected credentials");
                }
            }
        }
        curr_size = data.len();
    }
    Ok((data, fds))
}

impl Communicator {
    pub fn main_loop(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut msg_buf = Vec::new();
        loop {
            let mut fds = FdSet::new();
            fds.insert(self.app_stdout.as_raw_fd());
            fds.insert(self.comm_channel_recv.notify_recv.as_raw_fd());
            for external_app in self.external_apps.values() {
                fds.insert(external_app.as_raw_fd());
            }
            select(None, Some(&mut fds), None, None, None).unwrap();

            // Check if replies are pending
            if fds.contains(self.comm_channel_recv.notify_recv.as_raw_fd()) {
                let _ = self.comm_channel_recv.notify_recv.read().unwrap();

                // Send any pending replies
                let mut replies = vec![];
                while let Ok(reply) = self.comm_channel_recv.recv.try_recv() {
                    match reply {
                        FromStateMachine::Quit => {
                            // Got a Quit, closing the session!
                            info!("done");
                            return Ok(());
                        }
                        FromStateMachine::Reply(reply) => {
                            replies.push(reply);
                        }
                        FromStateMachine::RequestExternalWidget { scene_id, uri } => {
                            let uri = uri.strip_prefix("cmd:").unwrap();
                            let (cmd, rel_path) = uri.split_once("/").unwrap_or((uri, ""));
                            let external_app = self
                                .external_apps
                                .entry(cmd.to_string())
                                .or_insert_with(|| {
                                    let mut external_app = ExternalApp::spawn(&cmd);
                                    external_app.connect().unwrap();
                                    external_app
                                });
                            external_app.open(scene_id, rel_path)?;
                        }
                    }
                }
                if !replies.is_empty() {
                    self.app_stdin
                        .send(&boldui_protocol::R2AMessage::Update(R2AUpdate { replies }))?;
                }
            }

            // Check if new app inputs are pending
            if fds.contains(self.app_stdout.as_raw_fd()) {
                // Common quit logic
                let do_quit = || {
                    error!("Failed to read message from app, quitting");
                    self.event_loop_proxy.to_state_machine(ToStateMachine::Quit);
                };

                // Read message
                let msg_len = match self.app_stdout.read_u32::<LE>() {
                    Err(_) => {
                        do_quit();
                        return Ok(());
                    }
                    Ok(v) => v,
                };
                trace!("reading msg of size {msg_len}");
                msg_buf.resize(msg_len as usize, 0);
                if self.app_stdout.read_exact(&mut msg_buf).is_err() {
                    do_quit();
                    return Ok(());
                };
                let msg = bincode::deserialize::<A2RMessage>(&msg_buf)?;

                trace!("A2R: {:#?}", &msg);
                match msg {
                    A2RMessage::Update(update) => {
                        self.event_loop_proxy
                            .to_state_machine(ToStateMachine::Update(update));
                    }
                    A2RMessage::Error(e) => {
                        if e.code == 0 && e.text.is_empty() {
                            error!("App Quit");
                        } else {
                            error!(err_code = e.code, err_text = e.text, "App Error");
                        }
                        self.event_loop_proxy.to_state_machine(ToStateMachine::Quit);
                        return Ok(());
                    }
                    A2RMessage::CompressedUpdate(_msg) => unimplemented!(
                        "TODO: Implement zstd compressed payloads (for small binary sizes)"
                    ),
                }
            }

            // Check if new external app inputs are pending
            for external_app in self.external_apps.values_mut() {
                if fds.contains(external_app.as_raw_fd()) {
                    // Common quit logic
                    let do_quit = || {
                        // TODO: disconnect app instead
                        error!("Failed to read message from external app, quitting");
                        self.event_loop_proxy.to_state_machine(ToStateMachine::Quit);
                    };

                    // Read message
                    let (data, fds) = match read_with_fds(&mut external_app.sock, 8) {
                        Err(_) => {
                            do_quit();
                            return Ok(());
                        }
                        Ok(v) => v,
                    };
                    let msg_len = u32::from_le_bytes(data[0..4].try_into().unwrap());
                    let req_id = u32::from_le_bytes(data[4..8].try_into().unwrap());
                    // let msg_len = match external_app.sock.read_u32::<LE>() {
                    //     Err(_) => {
                    //         do_quit();
                    //         return Ok(());
                    //     }
                    //     Ok(v) => v,
                    // };
                    // let req_id = match external_app.sock.read_u32::<LE>() {
                    //     Err(_) => {
                    //         do_quit();
                    //         return Ok(());
                    //     }
                    //     Ok(v) => v,
                    // };
                    // let fds = read_fds(&mut external_app.sock);

                    trace!(
                        "reading msg of size {msg_len}, req_id={req_id}, fds={:?}",
                        fds
                    );
                    msg_buf.resize(msg_len as usize, 0);
                    if external_app.sock.read_exact(&mut msg_buf).is_err() {
                        do_quit();
                        return Ok(());
                    };
                    let msg = bincode::deserialize::<EA2RMessage>(&msg_buf)?;

                    trace!("EA2R: {:#?}", &msg);
                    let mut fds = fds.into_iter();
                    let fd = fds.next();
                    assert!(fds.next().is_none(), "More FDs than expected");
                    external_app.handle_message(req_id, msg, fd, self.event_loop_proxy.as_ref())?;
                }
            }
        }
    }
}
