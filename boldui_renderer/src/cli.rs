use argh::FromArgs;
use std::str::FromStr;

#[derive(Debug, Default)]
pub(crate) enum FrontendType {
    #[default]
    Image,
    Window,
}

impl FromStr for FrontendType {
    type Err = &'static str;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(match s {
            "image" => FrontendType::Image,
            "window" => FrontendType::Window,
            _ => return Err("Invalid frontend type, see --help"),
        })
    }
}

#[derive(FromArgs, Debug)]
/// Renderer for BoldUI applications
pub(crate) struct Params {
    // /// enable developer tools
    // #[argh(switch)]
    // pub devtools: bool,
    /// a uri to open inside the app
    #[argh(option, short = 'u')]
    pub uri: Option<String>,

    /// rendering frontend to use, one of: 'image' (default), 'window'
    #[argh(option)]
    pub frontend: Option<FrontendType>,
}

/// Extract the basename from a path
fn basename_of(path: &str) -> &str {
    std::path::Path::new(path)
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or(path)
}

pub(crate) fn get_params() -> (Params, Option<Vec<String>>) {
    let strings: Vec<String> = std::env::args().collect();
    let sep_idx = strings.iter().position(|s| s == "--");
    if let Some(sep_idx) = sep_idx {
        assert_ne!(sep_idx, 0);
    }

    let argv0 = basename_of(&strings[0]);
    let params_strs: Vec<&str> = sep_idx
        .map_or(&strings[..], |sep_idx| &strings[..sep_idx])
        .iter()
        .map(|s| s.as_str())
        .collect();
    let extra_strings = sep_idx.map(|sep_idx| strings[sep_idx + 1..].to_owned());

    let mut params = Params::from_args(&[argv0], &params_strs[1..]).unwrap_or_else(|early_exit| {
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
    });

    if params.frontend.is_none() {
        params.frontend = Some(FrontendType::default());
    }

    (params, extra_strings)
}