#![feature(unix_socket_ancillary_data)]
#![feature(io_error_more)]

extern crate core;

use crate::cli::{AppSubcommand, AttachSubcommand, ServerSubcommand, SubCommandEnum};
use crate::utils::unwrap_or_str;
use boldui_protocol::{WmHello, WmHelloAction, WM_REQ_MAGIC};
use std::io::IoSlice;
use std::mem::size_of;
use std::os::fd::AsFd;
use tokio_seqpacket::ancillary::AncillaryMessageWriter;
use tokio_seqpacket::UnixSeqpacket;
use tracing::info;
use tracing::subscriber::set_global_default;
use tracing_log::LogTracer;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::{EnvFilter, Registry};

pub mod cli;
pub mod server;
pub mod utils;

fn main() {
    const DEFAULT_SOCK: &str = "/run/user/1000/boldui_wm.sock";

    let params = cli::get_params();

    // Initialize logging
    LogTracer::init().expect("Failed to set logger");
    let env_filter = EnvFilter::try_from_default_env().unwrap_or(EnvFilter::new("info"));
    let formatting_layer = tracing_subscriber::fmt::layer().with_writer(std::io::stderr);
    // let journald_layer = tracing_journald::layer().expect("Failed to connect to journald");
    let subscriber = Registry::default().with(env_filter).with(formatting_layer);
    // .with(journald_layer);
    set_global_default(subscriber).expect("Failed to set subscriber");

    info!("WM Params: {:?}", params);

    match params.nested {
        SubCommandEnum::Server(ServerSubcommand { sock, composite }) => {
            do_server(unwrap_or_str(&sock, DEFAULT_SOCK), composite)
        }
        SubCommandEnum::App(AppSubcommand { sock, app_args }) => {
            tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .unwrap()
                .block_on(do_app(
                    unwrap_or_str(&sock, DEFAULT_SOCK),
                    &app_args.iter().map(|s| s.as_str()).collect::<Vec<&str>>(),
                ))
        }
        SubCommandEnum::Attach(AttachSubcommand { sock }) => {
            tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .unwrap()
                .block_on(do_attach(unwrap_or_str(&sock, DEFAULT_SOCK)))
        }
    }
}

fn do_server(sock_addr: &str, _composite: bool) {
    server::MainLoop::new().unwrap().run(sock_addr).unwrap();
}

async fn do_app(sock_addr: &str, app_args: &[&str]) {
    // Connect to control socket
    let sock = UnixSeqpacket::connect(sock_addr).await.unwrap();
    info!("args: {:?}", app_args);

    // Spawn app
    let mut proc = tokio::process::Command::new(app_args[0])
        .args(&app_args[1..])
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .unwrap();

    // Send hello to control socket, with the app's stdin/stdout fds
    let mut hello_buf = vec![];
    hello_buf.extend_from_slice(WM_REQ_MAGIC);
    unsafe {
        hello_buf.extend_from_slice(std::slice::from_raw_parts(
            &WmHello {
                action: WmHelloAction::ConnectApp,
            } as *const _ as *const u8,
            size_of::<WmHello>(),
        ));
    }
    info!("hello_buf: {:?}", hello_buf);

    let mut sa_buf = Vec::new();
    sa_buf.resize(256, 0u8);
    let mut sa = AncillaryMessageWriter::new(&mut sa_buf);

    let fds = &[
        proc.stdin.as_ref().unwrap().as_fd(),
        proc.stdout.as_ref().unwrap().as_fd(),
    ];
    info!("fds: {:?}", fds);
    sa.add_fds(fds).unwrap();
    sock.send_vectored_with_ancillary(&[IoSlice::new(&hello_buf)], &mut sa)
        .await
        .unwrap();

    // TODO: replace with execve(2), so we don't leave this useless process

    // Wait for app to exit, then exit with the same exit code
    let exit_status = proc.wait().await.unwrap();
    std::process::exit(exit_status.code().unwrap_or(1));
}

async fn do_attach(sock_addr: &str) {
    // Connect to control socket
    let sock = UnixSeqpacket::connect(sock_addr).await.unwrap();

    // Send hello to control socket, with our stdin/stdout fds
    let mut hello_buf = vec![];
    hello_buf.extend_from_slice(WM_REQ_MAGIC);
    unsafe {
        hello_buf.extend_from_slice(std::slice::from_raw_parts(
            &WmHello {
                action: WmHelloAction::AttachRenderer,
            } as *const _ as *const u8,
            size_of::<WmHello>(),
        ));
    }
    info!("hello_buf: {:?}", hello_buf);

    let mut sa_buf = Vec::new();
    sa_buf.resize(256, 0u8);
    let mut sa = AncillaryMessageWriter::new(&mut sa_buf);

    let stdin = std::io::stdin();
    let stdout = std::io::stdout();
    let fds = &[stdin.as_fd(), stdout.as_fd()];
    info!("fds: {:?}", fds);
    sa.add_fds(fds).unwrap();
    sock.send_vectored_with_ancillary(&[IoSlice::new(&hello_buf)], &mut sa)
        .await
        .unwrap();

    let mut buf = [0u8; 1];
    sock.recv(&mut buf).await.unwrap();
}
