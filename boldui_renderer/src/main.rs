#![feature(unix_socket_ancillary_data)]
#![allow(clippy::read_zero_byte_vec)] // False positives :(

use crate::cli::FrontendType;
use crate::communicator::{ConnectionInitiator, ToStateMachine};
use crate::image_frontend::ImageFrontend;
use crate::renderer::Renderer;
use crate::simulator::{SimulationFile, Simulator};
use crate::state_machine::StateMachine;
use crate::window_frontend::WindowFrontend;
use std::fs::File;
use std::os::unix::io::{FromRawFd, IntoRawFd};
use std::process::{Command, Stdio};
use tracing::debug;
use tracing::subscriber::set_global_default;
use tracing_log::LogTracer;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::{EnvFilter, Registry};
use util::SerdeSender;

pub(crate) mod cli;
// pub(crate) mod devtools;
pub(crate) mod communicator;
pub(crate) mod dmabuf;
pub(crate) mod image_frontend;
pub(crate) mod op_interpreter;
pub(crate) mod renderer;
pub(crate) mod simulator;
pub(crate) mod state_machine;
pub(crate) mod util;
pub(crate) mod window_frontend;

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
        .expect("Failed to spawn child");

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

    // Initialize logging
    LogTracer::init().expect("Failed to set logger");
    let env_filter = EnvFilter::try_from_default_env().unwrap_or(EnvFilter::new("info"));
    let formatting_layer = tracing_subscriber::fmt::layer().with_writer(std::io::stderr);
    // let journald_layer = tracing_journald::layer().expect("Failed to connect to journald");
    let subscriber = Registry::default().with(env_filter).with(formatting_layer);
    // .with(journald_layer);
    set_global_default(subscriber).expect("Failed to set subscriber");

    // Setup simulator
    let simulator = if let Some(dev_simulated_input) = params.dev_simulated_input {
        let simulated_input = std::fs::read_to_string(dev_simulated_input)?;
        let simulated_input: SimulationFile = serde_yaml::from_str(&simulated_input)?;
        Some(Simulator::new(simulated_input))
    } else {
        None
    };

    // Create child
    let extra = match extra {
        Some(extra) => extra,
        None => {
            eprintln!("Please specify an app to run. Example:");
            eprintln!("  cargo run -p boldui_renderer -- -- cargo run -p boldui_example_rs_calc");
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
    debug!("Starting boldui renderer");
    connect_init.connect()?;
    connect_init.send_open(params.uri.unwrap_or_else(|| "/".to_string()))?;

    let (mut frontend, event_proxy) = match params.frontend.unwrap() {
        FrontendType::Image => {
            let (frontend, event_proxy) =
                ImageFrontend::new(Renderer::new(), state_machine, simulator);
            (
                Box::new(frontend) as Box<dyn Frontend>,
                event_proxy as Box<dyn EventLoopProxy + Send>,
            )
        }
        FrontendType::Window => {
            let (frontend, event_proxy) =
                WindowFrontend::new(Renderer::new(), state_machine, simulator);
            (
                Box::new(frontend) as Box<dyn Frontend>,
                event_proxy as Box<dyn EventLoopProxy + Send>,
            )
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
