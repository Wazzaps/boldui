#![allow(clippy::absurd_extreme_comparisons)]

mod util;

use crate::util::SerdeSender;
use boldui_protocol::{
    A2RMessage, A2RReparentScene, A2RUpdate, A2RUpdateScene, CmdsCommand, Color, Error,
    HandlerBlock, HandlerCmd, OpId, OpsOperation, R2AMessage, R2AOpen, Value, VarId,
};
use byteorder::{ReadBytesExt, LE};
use std::collections::{BTreeMap, HashMap};
use std::io::{Read, Write};
use std::ops::Deref;
use uriparse::RelativeReference;

#[derive(Clone)]
struct OpWrapper(OpsOperation);

impl OpWrapper {
    pub fn push(self, scene: &mut OpFactory) -> OpIdWrapper {
        let scene_id = scene.0.id;
        let op_id = scene.0.ops.len() as u32;
        scene.0.ops.push(self.0);
        OpIdWrapper(OpId {
            scene_id,
            idx: op_id,
        })
    }
}

#[derive(Copy, Clone)]
struct OpIdWrapper(OpId);

impl Deref for OpIdWrapper {
    type Target = OpId;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

struct OpFactory<'a>(&'a mut A2RUpdateScene);

impl<'a> OpFactory<'a> {
    pub fn new_i64(val: i64) -> OpWrapper {
        OpWrapper(OpsOperation::Value(Value::Sint64(val)))
    }

    pub fn new_f64(val: f64) -> OpWrapper {
        OpWrapper(OpsOperation::Value(Value::Double(val)))
    }

    pub fn new_string(val: String) -> OpWrapper {
        OpWrapper(OpsOperation::Value(Value::String(val)))
    }

    pub fn new_color(val: Color) -> OpWrapper {
        OpWrapper(OpsOperation::Value(Value::Color(val)))
    }

    pub fn new_point(left: f64, top: f64) -> OpWrapper {
        OpWrapper(OpsOperation::Value(Value::Point { left, top }))
    }

    pub fn make_point(left: OpIdWrapper, top: OpIdWrapper) -> OpWrapper {
        OpWrapper(OpsOperation::MakePoint {
            left: *left,
            top: *top,
        })
    }

    pub fn new_rect(&mut self, left: f64, top: f64, right: f64, bottom: f64) -> OpWrapper {
        OpWrapper(OpsOperation::Value(Value::Rect {
            left,
            top,
            right,
            bottom,
        }))
    }

    pub fn make_rect_from_points(left_top: OpIdWrapper, right_bottom: OpIdWrapper) -> OpWrapper {
        OpWrapper(OpsOperation::MakeRectFromPoints {
            left_top: *left_top,
            right_bottom: *right_bottom,
        })
    }

    pub fn var<S: Into<String>>(&self, key: S) -> OpWrapper {
        let scene_id = self.0.id;
        OpWrapper(OpsOperation::Var(VarId {
            key: key.into(),
            scene: scene_id,
        }))
    }
}

impl std::ops::Add for OpIdWrapper {
    type Output = OpWrapper;

    fn add(self, rhs: Self) -> Self::Output {
        OpWrapper(OpsOperation::Add { a: *self, b: *rhs })
    }
}

impl std::ops::Neg for OpIdWrapper {
    type Output = OpWrapper;

    fn neg(self) -> Self::Output {
        OpWrapper(OpsOperation::Neg { a: *self })
    }
}

fn open_window(
    raw_path: String,
    path: &[&str],
    params: HashMap<String, String>,
    stdout: &mut impl SerdeSender,
) -> Result<(), Box<dyn std::error::Error>> {
    match path {
        // Root
        [""] => {
            let mut var_decls = BTreeMap::new();
            var_decls.insert("offset".to_string(), Value::Double(20.0));
            var_decls.insert(
                ":window_title".to_string(),
                Value::String("BoldUI Example: Shapes".to_string()),
            );
            var_decls.insert(":window_initial_size_x".to_string(), Value::Sint64(600));
            var_decls.insert(":window_initial_size_y".to_string(), Value::Sint64(400));
            if let Some(window_id) = params.get("window_id") {
                // Copy from input
                var_decls.insert(
                    ":window_id".to_string(),
                    Value::String(window_id.to_string()),
                );
            }

            let mut scene = A2RUpdateScene {
                id: 2,
                paint: OpId::default(),
                backdrop: OpId::default(),
                transform: OpId::default(),
                clip: OpId::default(),
                uri: format!(
                    "{}?session={}",
                    raw_path, "131a4feb-fe40-4ba4-b18b-4435d2874467"
                ),
                ops: vec![],
                cmds: vec![],
                var_decls,
            };

            {
                let f = &mut OpFactory(&mut scene);
                let clear_color = OpFactory::new_color(Color::from_hex(0x003333)).push(f);
                let rect_color = OpFactory::new_color(Color::from_hex(0x3A8DDA)).push(f);

                let offset = f.var("offset").push(f);
                let neg_offset = (-offset).push(f);
                let width = f.var(":width").push(f);
                let height = f.var(":height").push(f);

                let rect = OpFactory::make_rect_from_points(
                    OpFactory::make_point(offset, offset).push(f),
                    OpFactory::make_point(
                        (width + neg_offset).push(f),
                        (height + neg_offset).push(f),
                    )
                    .push(f),
                )
                .push(f);

                scene.cmds.push(CmdsCommand::Clear {
                    color: *clear_color,
                });
                scene.cmds.push(CmdsCommand::DrawRect {
                    paint: *rect_color,
                    rect: *rect,
                });
            }

            stdout.send(&A2RMessage::Update(A2RUpdate {
                updated_scenes: vec![scene],
                run_blocks: vec![
                    // Reparent the scene(s)
                    HandlerBlock {
                        ops: vec![],
                        cmds: vec![HandlerCmd::ReparentScene {
                            scene: 2,
                            to: A2RReparentScene::Root,
                        }],
                    },
                ],
            }))?;

            stdout.send(&A2RMessage::Update(A2RUpdate {
                updated_scenes: vec![],
                run_blocks: vec![
                    // Change offset
                    HandlerBlock {
                        ops: vec![
                            // Op #0
                            OpsOperation::Value(Value::Double(100.0)),
                        ],
                        cmds: vec![HandlerCmd::UpdateVar {
                            var: VarId {
                                key: "offset".to_string(),
                                scene: 2,
                            },
                            value: OpId {
                                scene_id: 0,
                                idx: 0,
                            },
                        }],
                    },
                ],
            }))?;
        }

        // Not found
        _ => {
            stdout.send(&A2RMessage::Error(Error {
                code: 1,
                text: format!("Not found: {:?}", path),
            }))?;
        }
    };
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    if atty::is(atty::Stream::Stdout) || atty::is(atty::Stream::Stdin) {
        eprintln!("Run this app like so:");
        eprintln!("  cargo run -p boldui_renderer -- -- cargo run -p boldui_example_shapes");
        std::process::exit(1);
    }

    let mut stdout = std::io::stdout().lock();
    let mut stdin = std::io::stdin().lock();

    // Get hello
    {
        eprintln!("[app:dbg] reading hello");
        let mut magic = [0u8; boldui_protocol::R2A_MAGIC.len()];
        stdin.read_exact(&mut magic).unwrap();
        assert_eq!(&magic, boldui_protocol::R2A_MAGIC, "Missing magic");

        let hello = bincode::deserialize_from::<_, boldui_protocol::R2AHello>(&mut stdin)?;
        assert!(
            boldui_protocol::LATEST_MAJOR_VER <= hello.max_protocol_major_version
                && (boldui_protocol::LATEST_MAJOR_VER > hello.min_protocol_major_version
                    || (boldui_protocol::LATEST_MAJOR_VER == hello.min_protocol_major_version
                        && boldui_protocol::LATEST_MINOR_VER >= hello.min_protocol_minor_version)),
            "[app:err] Incompatible version"
        );
        assert_eq!(
            hello.extra_len, 0,
            "[app:err] This protocol version specifies no extra data"
        );
    }

    // Reply with A2RHelloResponse
    {
        eprintln!("[app:dbg] sending hello response");
        stdout.write_all(boldui_protocol::A2R_MAGIC)?;
        stdout.write_all(&bincode::serialize(&boldui_protocol::A2RHelloResponse {
            protocol_major_version: boldui_protocol::LATEST_MAJOR_VER,
            protocol_minor_version: boldui_protocol::LATEST_MINOR_VER,
            extra_len: 0,
            error: None,
            // error: Some(boldui_protocol::CommonError {
            //     code: 123,
            //     text: "Foo".to_string(),
            // }),
        })?)?;
        stdout.flush()?;
        eprintln!("[app:dbg] connected!");
    }

    let mut msg_buf = Vec::new();
    loop {
        let msg_len = stdin.read_u32::<LE>()?;
        eprintln!("[app:dbg] reading msg of size {}", msg_len);
        msg_buf.resize(msg_len as usize, 0);
        stdin.read_exact(&mut msg_buf)?;
        let msg = bincode::deserialize::<R2AMessage>(&msg_buf)?;

        eprintln!("[app:dbg] R2A: {:#?}", &msg);
        match msg {
            R2AMessage::Update(_) => {}
            R2AMessage::Open(R2AOpen { path }) => {
                fn parse_path(path: &str) -> (String, Vec<String>, Vec<(String, String)>) {
                    let reference = RelativeReference::try_from(path).unwrap();
                    let segments: Vec<String> = reference
                        .path()
                        .segments()
                        .iter()
                        .map(|s| {
                            let mut seg = s.to_owned();
                            seg.normalize();
                            seg.to_string()
                        })
                        .collect();

                    let query = reference
                        .query()
                        .map(|query| {
                            let mut query = query.to_owned();
                            query.normalize();
                            querystring::querify(query.as_str())
                                .into_iter()
                                .map(|q| (q.0.to_string(), q.1.to_string()))
                                .collect::<Vec<_>>()
                        })
                        .unwrap_or_else(Vec::new);

                    (reference.path().to_string(), segments, query)
                }

                let (raw_path, path, params) = parse_path(&path);

                let path_ref = &*path.iter().map(|p| p.as_str()).collect::<Vec<_>>();
                let params_map = {
                    let mut map = HashMap::new();
                    for (k, v) in params.into_iter() {
                        map.insert(k, v);
                    }
                    map
                };

                open_window(raw_path, path_ref, params_map, &mut stdout)?;
            }
            R2AMessage::Error(_) => {}
        }
    }
}
