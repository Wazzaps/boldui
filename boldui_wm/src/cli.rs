use argh::FromArgs;

#[derive(FromArgs, Debug)]
/// Renderer for BoldUI applications
pub(crate) struct Params {
    #[argh(subcommand)]
    pub nested: SubCommandEnum,
}

#[derive(FromArgs, PartialEq, Debug)]
#[argh(subcommand)]
pub(crate) enum SubCommandEnum {
    Server(ServerSubcommand),
    App(AppSubcommand),
    Attach(AttachSubcommand),
}

#[derive(FromArgs, PartialEq, Debug)]
/// Start a window manager for apps to connect to
#[argh(subcommand, name = "server")]
pub(crate) struct ServerSubcommand {
    /// path to unix socket to listen on (default: /run/user/1000/boldui_wm.sock)
    #[argh(option)]
    pub sock: Option<String>,

    /// enable this to combine all windows into a single window
    #[argh(switch)]
    pub composite: bool,
}

#[derive(FromArgs, PartialEq, Debug)]
/// Connect an app to the currently running window manager
#[argh(subcommand, name = "app")]
pub(crate) struct AppSubcommand {
    /// path to unix socket to connect to
    #[argh(option)]
    pub sock: Option<String>,

    #[argh(positional, greedy)]
    pub app_args: Vec<String>,
}

#[derive(FromArgs, PartialEq, Debug)]
/// Display the currently running window manager using a renderer
#[argh(subcommand, name = "attach")]
pub(crate) struct AttachSubcommand {
    /// path to unix socket to connect to
    #[argh(option)]
    pub sock: Option<String>,
}

/// Extract the basename from a path
fn basename_of(path: &str) -> &str {
    std::path::Path::new(path)
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or(path)
}

pub(crate) fn get_params() -> Params {
    let strings: Vec<String> = std::env::args().collect();
    let argv0 = basename_of(&strings[0]);
    let params_strs: Vec<&str> = strings[1..].iter().map(|s| s.as_str()).collect();

    Params::from_args(&[argv0], &params_strs).unwrap_or_else(|early_exit| {
        std::process::exit(match early_exit.status {
            Ok(()) => {
                println!("{}", early_exit.output);
                0
            }
            Err(()) => {
                eprintln!(
                    "{}\nRun {} --help for more information.",
                    early_exit.output, argv0
                );
                1
            }
        })
    })
}
