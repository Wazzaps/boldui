use crate::StateMachine;
use boldui_protocol::serde::Deserialize;

#[derive(Deserialize)]
pub enum Instruction {
    Sleep { time_ms: u64 },
    Click { x: f64, y: f64, button: u8 },
}

#[derive(Deserialize)]
pub struct SimulationFile {
    format_version: String,
    instructions: Vec<Instruction>,
}

pub(crate) struct Simulator {
    src: SimulationFile,
}

impl Simulator {
    pub fn new(src: SimulationFile) -> Self {
        Self { src }
    }

    pub fn tick(&self, state_machine: &mut StateMachine) {
        todo!();
    }
}
