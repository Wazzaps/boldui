use crate::{SerdeSender, StateMachine};
use boldui_protocol::{bincode, A2RMessage, A2RUpdate};
use byteorder::{ReadBytesExt, LE};
use parking_lot::Mutex;
use std::io::{Read, Write};
use std::sync::{Arc, Barrier};

pub(crate) struct Communicator<'a> {
    pub app_stdin: Box<dyn Write + Send>,
    pub app_stdout: Box<dyn Read + Send>,
    pub state_machine: &'a Mutex<StateMachine>,
    pub update_barrier: Option<Arc<Barrier>>,
}

impl<'a> Communicator<'a> {
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

    pub fn main_loop(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut msg_buf = Vec::new();
        loop {
            let msg_len = self.app_stdout.read_u32::<LE>()?;
            eprintln!("[rnd:dbg] reading msg of size {}", msg_len);
            msg_buf.resize(msg_len as usize, 0);
            self.app_stdout.read_exact(&mut msg_buf)?;
            let msg = bincode::deserialize::<A2RMessage>(&msg_buf)?;

            eprintln!("[rnd:dbg] A2R: {:#?}", &msg);
            match msg {
                A2RMessage::Update(A2RUpdate {
                    updated_scenes,
                    run_blocks,
                }) => {
                    // Some frontends (e.g. image frontend) want to run between _each_ update, so wait for it to finish
                    if let Some(update_barrier) = &self.update_barrier {
                        update_barrier.wait();
                    }

                    // TODO: Create utilities for some of the repeated code here
                    let mut state = self.state_machine.lock();

                    state.update_scenes_and_run_blocks(updated_scenes, run_blocks);
                }
                A2RMessage::Error(e) => {
                    panic!("App Error: Code {}: {}", e.code, e.text);
                }
            }
        }
    }
}
