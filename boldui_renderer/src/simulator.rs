use crate::communicator::FromStateMachine;
use crate::{StateMachine, ToStateMachine};
use boldui_protocol::serde::Deserialize;
use std::error::Error;
use std::time::{Duration, Instant};

#[derive(Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Instruction {
    Sleep { time_ms: u64 },
    Click { x: f64, y: f64, button: u8 },
    WaitForUpdate,
    Quit,
}

#[derive(Deserialize)]
pub struct SimulationFile {
    format_version: String,
    instructions: Vec<Instruction>,
}

pub(crate) struct Simulator {
    src: SimulationFile,
    next_wakeup: Option<Instant>,
    curr_insn: usize,
}

impl Simulator {
    pub fn new(src: SimulationFile) -> Self {
        assert_eq!(src.format_version, "0");
        eprintln!("[rnd:dbg] simulator: opcode #0");
        Self {
            src,
            next_wakeup: None,
            curr_insn: 0,
        }
    }

    pub fn tick(
        &mut self,
        state_machine: &mut StateMachine,
        mut did_just_update: bool,
    ) -> Result<(), Box<dyn Error>> {
        loop {
            if self.curr_insn >= self.src.instructions.len() {
                // Program done
                break;
            }
            if let Some(next_wakeup) = self.next_wakeup {
                let now = Instant::now();
                if now >= next_wakeup {
                    // Waking up, end the current (sleep) instruction
                    self.curr_insn += 1;
                    self.next_wakeup = None;
                    continue;
                }
            }

            match self.src.instructions[self.curr_insn] {
                Instruction::Sleep { time_ms } => {
                    let next_wakeup = Instant::now() + Duration::from_millis(time_ms);
                    self.next_wakeup = Some(next_wakeup);
                    self.send_event(state_machine, ToStateMachine::SleepUntil(next_wakeup));
                    break;
                }
                Instruction::Click { x, y, button } => {
                    self.send_event(state_machine, ToStateMachine::Click { x, y, button });
                }
                Instruction::Quit => {
                    self.curr_insn += 1;
                    self.send_event(state_machine, ToStateMachine::Quit);
                    self.send_comm_event(state_machine, FromStateMachine::Quit)?;
                    break;
                }
                Instruction::WaitForUpdate => {
                    if !did_just_update {
                        break;
                    } else {
                        did_just_update = false;
                    }
                }
            }

            // Next opcode!
            self.curr_insn += 1;
            eprintln!("[rnd:dbg] simulator: opcode #{}", self.curr_insn);
        }
        Ok(())
    }

    fn send_event(&mut self, state_machine: &mut StateMachine, event: ToStateMachine) {
        state_machine
            .event_proxy
            .as_ref()
            .unwrap()
            .to_state_machine(event);
    }

    fn send_comm_event(
        &mut self,
        state_machine: &mut StateMachine,
        event: FromStateMachine,
    ) -> Result<(), Box<dyn Error>> {
        state_machine.comm_channel_send.send.send(event)?;
        state_machine.comm_channel_send.notify_send.write(1)?;
        Ok(())
    }
}
