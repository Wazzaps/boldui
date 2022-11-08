use crate::{EventLoopProxy, SerdeSender};
use boldui_protocol::{bincode, A2RMessage, A2RUpdate, R2AReply, R2AUpdate};
use byteorder::{ReadBytesExt, LE};
use crossbeam::channel::{Receiver, Sender};
use eventfd::EventFD;
use nix::sys::select::{select, FdSet};
use std::fs::File;
use std::io::{Read, Write};
use std::os::unix::io::AsRawFd;

pub(crate) enum ToStateMachine {
    Quit,
    Redraw,
    Update(A2RUpdate),
}

pub(crate) enum FromStateMachine {
    Quit,
    Reply(R2AReply),
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
    pub event_loop_proxy: Box<dyn EventLoopProxy + Send>,
    pub comm_channel_recv: CommChannelRecv,
}

impl ConnectionInitiator {
    pub fn connect(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // Send hello
        {
            eprintln!("[rnd:dbg] sending hello");

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
            eprintln!("[rnd:dbg] reading hello response");
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
                "[rnd:err] Incompatible version"
            );
            assert_eq!(
                hello_res.extra_len, 0,
                "[rnd:err] This protocol version specifies no extra data"
            );

            if let Some(err) = hello_res.error {
                panic!(
                    "[rnd:err] An error has occurred: code {}: {}",
                    err.code, err.text
                );
            }
            eprintln!("[rnd:dbg] connected!");
        }
        Ok(())
    }

    pub fn send_open(&mut self, path: String) -> Result<(), Box<dyn std::error::Error>> {
        eprintln!("[rnd:dbg] sending R2AOpen");
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
        }
    }
}

impl Communicator {
    pub fn main_loop(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut msg_buf = Vec::new();
        loop {
            let mut fds = FdSet::new();
            fds.insert(self.app_stdout.as_raw_fd());
            fds.insert(self.comm_channel_recv.notify_recv.as_raw_fd());
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
                            eprintln!("[rnd:dbg] done");
                            return Ok(());
                        }
                        FromStateMachine::Reply(reply) => {
                            replies.push(reply);
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
                let msg_len = self.app_stdout.read_u32::<LE>()?;
                eprintln!("[rnd:dbg] reading msg of size {}", msg_len);
                msg_buf.resize(msg_len as usize, 0);
                self.app_stdout.read_exact(&mut msg_buf)?;
                let msg = bincode::deserialize::<A2RMessage>(&msg_buf)?;

                // eprintln!("[rnd:dbg] A2R: {:#?}", &msg);
                match msg {
                    A2RMessage::Update(update) => {
                        self.event_loop_proxy
                            .to_state_machine(ToStateMachine::Update(update));
                    }
                    A2RMessage::Error(e) => {
                        if e.code == 0 && e.text.is_empty() {
                            eprintln!("[rnd:err] App Quit");
                        } else {
                            eprintln!("[rnd:err] App Error: Code {}: {}", e.code, e.text);
                        }
                        self.event_loop_proxy.to_state_machine(ToStateMachine::Quit);
                        return Ok(());
                    }
                    A2RMessage::CompressedUpdate(_msg) => unimplemented!(
                        "TODO: Implement zstd compressed payloads (for small binary sizes)"
                    ),
                }
            }
        }
    }
}
