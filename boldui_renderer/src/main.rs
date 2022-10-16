use crate::cli::FrontendType;
use crate::image_frontend::ImageFrontend;
use crate::renderer::Renderer;
use crate::state_machine::StateMachine;
use communicator::Communicator;
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
pub(crate) mod state_machine;
pub(crate) mod util;

pub(crate) trait EventLoopProxy {
    fn request_redraw(&self);
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
    let (state_machine, from_frontend_recv, from_frontend_notify_recv) = StateMachine::new();
    let mut communicator = Communicator {
        app_stdin: inp,
        app_stdout: out,
        state_machine: &state_machine,
        update_barrier: None,
        from_frontend_recv,
        from_frontend_notify_recv,
    };
    communicator.connect()?;
    communicator.send_open(params.uri.unwrap_or_else(|| "/".to_string()))?;

    let (mut frontend, wakeup_proxy, update_barrier) = match params.frontend.unwrap() {
        FrontendType::Image => {
            let (frontend, wakeup_proxy, update_barrier) =
                ImageFrontend::new(Renderer {}, &state_machine);
            (
                Box::new(frontend) as Box<dyn Frontend>,
                Box::new(wakeup_proxy) as Box<dyn EventLoopProxy + Send>,
                Some(update_barrier),
            )
        }
        FrontendType::Window => {
            unimplemented!()
        }
    };

    state_machine.lock().wakeup_proxy = Some(wakeup_proxy);
    communicator.update_barrier = update_barrier;

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
