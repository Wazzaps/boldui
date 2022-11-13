use crate::cli::FrontendType;
use crate::communicator::{ConnectionInitiator, ToStateMachine};
use crate::image_frontend::ImageFrontend;
use crate::renderer::Renderer;
use crate::simulator::{SimulationFile, Simulator};
use crate::state_machine::StateMachine;
use std::fs::File;
use std::os::unix::io::{FromRawFd, IntoRawFd};
use std::process::{Command, Stdio};
use util::SerdeSender;

pub(crate) mod cli;
// pub(crate) mod devtools;
pub(crate) mod communicator;
pub(crate) mod image_frontend;
pub(crate) mod op_interpreter;
pub(crate) mod renderer;
pub(crate) mod simulator;
pub(crate) mod state_machine;
pub(crate) mod util;

pub(crate) trait EventLoopProxy {
    fn to_state_machine(&self, event: ToStateMachine);
}

pub(crate) trait Frontend {
    fn main_loop(&mut self);
}

fn create_child(extra: Vec<String>) -> (File, File) {
    let mut cmd = Command::new(&extra[0])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .args(&extra[1..])
        .spawn()
        .expect("[rnd:err] Failed to spawn child");

    // SAFETY: These FDs were given to us by the `Command`, and will not be closed by themselves
    unsafe {
        (
            File::from_raw_fd(cmd.stdin.take().unwrap().into_raw_fd()),
            File::from_raw_fd(cmd.stdout.take().unwrap().into_raw_fd()),
        )
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let (params, extra) = cli::get_params();
    // println!("Command line args: {:?}, Extra: {:?}", &params, &extra);

    let simulator = if let Some(dev_simulated_input) = params.dev_simulated_input {
        let simulated_input = std::fs::read_to_string(&dev_simulated_input)?;
        let simulated_input: SimulationFile = serde_json::from_str(&simulated_input)?;
        Some(Simulator::new(simulated_input))
    } else {
        None
    };

    // Create child
    let extra = match extra {
        Some(extra) => extra,
        None => {
            eprintln!("Please specify an app to run. Example:");
            eprintln!("  cargo run -p boldui_renderer -- -- cargo run -p boldui_example_shapes");
            std::process::exit(1);
        }
    };
    let (inp, out) = create_child(extra);

    // Connect
    let (state_machine, comm_channel_recv) = StateMachine::new();
    let mut connect_init = ConnectionInitiator {
        app_stdin: inp,
        app_stdout: out,
        // update_barrier: None,
    };
    connect_init.connect()?;
    connect_init.send_open(params.uri.unwrap_or_else(|| "/".to_string()))?;

    let (mut frontend, event_proxy) = match params.frontend.unwrap() {
        FrontendType::Image => {
            let (frontend, event_proxy) =
                ImageFrontend::new(Renderer::new(), state_machine, simulator);
            (Box::new(frontend) as Box<dyn Frontend>, event_proxy)
        }
        FrontendType::Window => {
            unimplemented!()
        }
    };

    let mut communicator = connect_init.into_communicator(event_proxy, comm_channel_recv);

    crossbeam::scope(|scope| {
        scope.spawn(|_| {
            communicator.main_loop().unwrap();
        });
        frontend.main_loop();
    })
    .unwrap();

    // devtools::main();

    Ok(())
}
