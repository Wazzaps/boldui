#![allow(clippy::absurd_extreme_comparisons)]

mod util;

use crate::util::SerdeSender;
use boldui_protocol::{
    A2RMessage, A2RReparentScene, A2RUpdate, A2RUpdateScene, CmdsCommand, Color, Error, EventType,
    HandlerBlock, HandlerCmd, OpId, OpsOperation, R2AMessage, R2AOpen, R2AUpdate, Value, VarId,
};
use byteorder::{ReadBytesExt, LE};
use std::collections::{BTreeMap, HashMap};
use std::io::{ErrorKind, Read, Write};
use std::ops::Deref;
use std::time::Instant;
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

#[allow(dead_code)]
impl OpIdWrapper {
    fn equals(self, rhs: OpIdWrapper) -> OpWrapper {
        OpWrapper(OpsOperation::Eq { a: *self, b: *rhs })
    }
}

struct OpFactory<'a>(&'a mut A2RUpdateScene);

#[allow(dead_code)]
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

    pub fn new_rect(left: f64, top: f64, right: f64, bottom: f64) -> OpWrapper {
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

    pub fn push_cmd(&mut self, cmd: CmdsCommand) {
        self.0.cmds.push(cmd);
    }

    pub fn push_event_handler(&mut self, evt_type: EventType, handler: HandlerBlock) {
        self.0.event_handlers.push((evt_type, handler));
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
            let start = Instant::now();
            let mut var_decls = BTreeMap::new();
            var_decls.insert("offset".to_string(), Value::Double(20.0));
            var_decls.insert(
                ":window_title".to_string(),
                Value::String("BoldUI Example: Calculator".to_string()),
            );
            var_decls.insert(":window_initial_size_x".to_string(), Value::Sint64(334));
            var_decls.insert(":window_initial_size_y".to_string(), Value::Sint64(327));
            if let Some(window_id) = params.get("window_id") {
                // Copy from input
                var_decls.insert(
                    ":window_id".to_string(),
                    Value::String(window_id.to_string()),
                );
            }

            let mut scene = A2RUpdateScene {
                id: 1,
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
                watches: vec![],
                event_handlers: vec![],
            };

            {
                let f = &mut OpFactory(&mut scene);

                // Background
                let bg_color = OpFactory::new_color(Color::from_hex(0x242424)).push(f);
                f.push_cmd(CmdsCommand::Clear { color: *bg_color });

                // Results box
                let result_bg_color = OpFactory::new_color(Color::from_hex(0x363636)).push(f);
                const RESULTS_WIDTH: f64 = 334.0;
                const RESULTS_HEIGHT: f64 = 65.0;
                let results_rect =
                    OpFactory::new_rect(0.0, 1.0, RESULTS_WIDTH, RESULTS_HEIGHT + 1.0).push(f);
                f.push_cmd(CmdsCommand::DrawRect {
                    paint: *result_bg_color,
                    rect: *results_rect,
                });

                let result_text_color = OpFactory::new_color(Color::from_hex(0xffffff)).push(f);
                // const RESULT_LEFT_PADDING: f64 = 16.0;
                let text_pos =
                    OpFactory::new_point(RESULTS_WIDTH / 2.0, RESULTS_HEIGHT / 2.0).push(f);
                let text = OpFactory::new_string("0".to_string()).push(f);
                f.push_cmd(CmdsCommand::DrawCenteredText {
                    text: *text,
                    paint: *result_text_color,
                    center: *text_pos,
                });

                // Buttons: Row 1
                let action_button_color = OpFactory::new_color(Color::from_hex(0x3a3a3a)).push(f);
                let number_button_color = OpFactory::new_color(Color::from_hex(0x505050)).push(f);
                let equals_button_color = OpFactory::new_color(Color::from_hex(0xe66100)).push(f);
                let button_text_color = OpFactory::new_color(Color::from_hex(0xffffff)).push(f);

                fn make_btn(
                    f: &mut OpFactory,
                    color: OpId,
                    x: i32,
                    y: i32,
                    text: &str,
                    text_color: OpId,
                ) {
                    const TOP_PADDING: f64 = 79.0;
                    const LEFT_PADDING: f64 = 12.0;
                    const X_PADDING: f64 = 4.0;
                    const Y_PADDING: f64 = 4.0;
                    const BTN_WIDTH: f64 = 59.0;
                    const BTN_HEIGHT: f64 = 44.0;

                    let rect = OpFactory::new_rect(
                        LEFT_PADDING + (x as f64) * (X_PADDING + BTN_WIDTH),
                        TOP_PADDING + (y as f64) * (Y_PADDING + BTN_HEIGHT),
                        LEFT_PADDING + (x as f64) * (X_PADDING + BTN_WIDTH) + BTN_WIDTH,
                        TOP_PADDING + (y as f64) * (Y_PADDING + BTN_HEIGHT) + BTN_HEIGHT,
                    )
                    .push(f);
                    f.push_cmd(CmdsCommand::DrawRect {
                        paint: color,
                        rect: *rect,
                    });

                    let text_pos = OpFactory::new_point(
                        LEFT_PADDING + (x as f64) * (X_PADDING + BTN_WIDTH) + 0.5 * BTN_WIDTH,
                        TOP_PADDING + (y as f64) * (Y_PADDING + BTN_HEIGHT) + 0.5 * BTN_HEIGHT,
                    )
                    .push(f);
                    let text_op = OpFactory::new_string(text.to_string()).push(f);
                    f.push_cmd(CmdsCommand::DrawCenteredText {
                        text: *text_op,
                        paint: text_color,
                        center: *text_pos,
                    });

                    // Click handler
                    f.push_event_handler(
                        EventType::Click { rect: *rect },
                        HandlerBlock {
                            ops: vec![],
                            cmds: vec![
                                HandlerCmd::DebugMessage {
                                    msg: text.to_string(),
                                },
                                // HandlerCmd::Reply {
                                //     path: "/".to_string(),
                                //     params: vec![*text_op],
                                // },
                            ],
                        },
                    );
                }

                fn make_tall_btn(
                    f: &mut OpFactory,
                    color: OpId,
                    x: i32,
                    y: i32,
                    text: &str,
                    text_color: OpId,
                ) {
                    const TOP_PADDING: f64 = 79.0;
                    const LEFT_PADDING: f64 = 12.0;
                    const X_PADDING: f64 = 4.0;
                    const Y_PADDING: f64 = 4.0;
                    const BTN_WIDTH: f64 = 59.0;
                    const BTN_HEIGHT: f64 = 44.0;

                    let rect = OpFactory::new_rect(
                        LEFT_PADDING + (x as f64) * (X_PADDING + BTN_WIDTH),
                        TOP_PADDING + (y as f64) * (Y_PADDING + BTN_HEIGHT),
                        LEFT_PADDING + (x as f64) * (X_PADDING + BTN_WIDTH) + BTN_WIDTH,
                        TOP_PADDING + ((y + 1) as f64) * (Y_PADDING + BTN_HEIGHT) + BTN_HEIGHT,
                    )
                    .push(f);
                    f.push_cmd(CmdsCommand::DrawRect {
                        paint: color,
                        rect: *rect,
                    });

                    let text_pos = OpFactory::new_point(
                        LEFT_PADDING + (x as f64) * (X_PADDING + BTN_WIDTH) + 0.5 * BTN_WIDTH,
                        TOP_PADDING + (y as f64) * (Y_PADDING + BTN_HEIGHT) + 1.0 * BTN_HEIGHT,
                    )
                    .push(f);
                    let text_op = OpFactory::new_string(text.to_string()).push(f);
                    f.push_cmd(CmdsCommand::DrawCenteredText {
                        text: *text_op,
                        paint: text_color,
                        center: *text_pos,
                    });

                    // Click handler
                    f.push_event_handler(
                        EventType::Click { rect: *rect },
                        HandlerBlock {
                            ops: vec![],
                            cmds: vec![
                                HandlerCmd::DebugMessage {
                                    msg: text.to_string(),
                                },
                                // HandlerCmd::Reply {
                                //     path: "/".to_string(),
                                //     params: vec![*text_op],
                                // },
                            ],
                        },
                    );
                }

                // Row 1
                // Backspace
                make_btn(f, *action_button_color, 0, 0, "<x|", *button_text_color);

                // Left Bracket
                make_btn(f, *action_button_color, 1, 0, "(", *button_text_color);

                // Right Bracket
                make_btn(f, *action_button_color, 2, 0, ")", *button_text_color);

                // Mod
                make_btn(f, *action_button_color, 3, 0, "mod", *button_text_color);

                // Pi
                make_btn(f, *action_button_color, 4, 0, "pi", *button_text_color);

                // Row 2
                // 7
                make_btn(f, *number_button_color, 0, 1, "7", *button_text_color);

                // 8
                make_btn(f, *number_button_color, 1, 1, "8", *button_text_color);

                // 9
                make_btn(f, *number_button_color, 2, 1, "9", *button_text_color);

                // Div
                make_btn(f, *action_button_color, 3, 1, "/", *button_text_color);

                // Sqrt
                make_btn(f, *action_button_color, 4, 1, "sqrt", *button_text_color);

                // Row 3
                // 4
                make_btn(f, *number_button_color, 0, 2, "4", *button_text_color);

                // 5
                make_btn(f, *number_button_color, 1, 2, "5", *button_text_color);

                // 6
                make_btn(f, *number_button_color, 2, 2, "6", *button_text_color);

                // Mult
                make_btn(f, *action_button_color, 3, 2, "*", *button_text_color);

                // x^2
                make_btn(f, *action_button_color, 4, 2, "x^2", *button_text_color);

                // Row 4
                // 1
                make_btn(f, *number_button_color, 0, 3, "1", *button_text_color);

                // 2
                make_btn(f, *number_button_color, 1, 3, "2", *button_text_color);

                // 3
                make_btn(f, *number_button_color, 2, 3, "3", *button_text_color);

                // Sub
                make_btn(f, *action_button_color, 3, 3, "-", *button_text_color);

                // Equals
                make_tall_btn(f, *equals_button_color, 4, 3, "=", *button_text_color);

                // Row 5
                // 0
                make_btn(f, *number_button_color, 0, 4, "0", *button_text_color);

                // Dot
                make_btn(f, *action_button_color, 1, 4, ".", *button_text_color);

                // Percent
                make_btn(f, *action_button_color, 2, 4, "%", *button_text_color);

                // Plus
                make_btn(f, *action_button_color, 3, 4, "+", *button_text_color);

                // let rect_color = OpFactory::new_color(Color::from_hex(0x3A8DDA)).push(f);
                //
                // let offset = f.var("offset").push(f);
                // let neg_offset = (-offset).push(f);
                // let width = f.var(":width").push(f);
                // let height = f.var(":height").push(f);
                //
                // let rect = OpFactory::make_rect_from_points(
                //     OpFactory::make_point(offset, offset).push(f),
                //     OpFactory::make_point(
                //         (width + neg_offset).push(f),
                //         (height + neg_offset).push(f),
                //     )
                //     .push(f),
                // )
                // .push(f);
                //
                // let offset_eq_100 = offset.equals(OpFactory::new_f64(100.0).push(f)).push(f);
                //
                // scene.cmds.push(CmdsCommand::DrawRect {
                //     paint: *rect_color,
                //     rect: *rect,
                // });
                // scene.watches.push(Watch {
                //     condition: *offset_eq_100,
                //     handler: HandlerBlock {
                //         ops: vec![],
                //         cmds: vec![
                //             HandlerCmd::DebugMessage {
                //                 msg: "Offset is 100.0, sending reply".to_string(),
                //             },
                //             HandlerCmd::Reply {
                //                 path: "/".to_string(),
                //                 params: vec![*width, *height],
                //             },
                //         ],
                //     },
                // });

                // for i in 0..256 {
                //     let color = OpFactory::new_color(Color::from_hex(0xe66100 + i)).push(f);
                //     let rect =
                //         OpFactory::new_rect(i as f64, i as f64, i as f64 + 30.0, i as f64 + 30.0)
                //             .push(f);
                //     f.push_cmd(CmdsCommand::DrawRect {
                //         paint: *color,
                //         rect: *rect,
                //     });
                // }
            }

            stdout.send(&A2RMessage::Update(A2RUpdate {
                updated_scenes: vec![scene],
                run_blocks: vec![
                    // Reparent the scene(s)
                    HandlerBlock {
                        ops: vec![],
                        cmds: vec![HandlerCmd::ReparentScene {
                            scene: 1,
                            to: A2RReparentScene::Root,
                        }],
                    },
                ],
            }))?;

            stdout.send(&A2RMessage::Update(A2RUpdate {
                updated_scenes: vec![],
                run_blocks: vec![],
            }))?;

            // stdout.send(&A2RMessage::Update(A2RUpdate {
            //     updated_scenes: vec![],
            //     run_blocks: vec![
            //         // Change offset
            //         HandlerBlock {
            //             ops: vec![
            //                 // Op #0
            //                 OpsOperation::Value(Value::Double(100.0)),
            //             ],
            //             cmds: vec![HandlerCmd::UpdateVar {
            //                 var: VarId {
            //                     key: "offset".to_string(),
            //                     scene: 1,
            //                 },
            //                 value: OpId {
            //                     scene_id: 0,
            //                     idx: 0,
            //                 },
            //             }],
            //         },
            //     ],
            // }))?;

            eprintln!("[app:dbg] Scene update took {:?} to make", start.elapsed());
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
        let msg_len = stdin.read_u32::<LE>();
        let msg_len = match msg_len {
            Ok(len) => len,
            Err(e) if e.kind() == ErrorKind::UnexpectedEof => {
                eprintln!("[app:dbg] connection closed, bye!");
                return Ok(());
            }
            Err(e) => Err(e)?,
        };

        eprintln!("[app:dbg] reading msg of size {}", msg_len);
        msg_buf.resize(msg_len as usize, 0);
        stdin.read_exact(&mut msg_buf)?;
        let msg = bincode::deserialize::<R2AMessage>(&msg_buf)?;

        // eprintln!("[app:dbg] R2A: {:#?}", &msg);
        match msg {
            R2AMessage::Update(R2AUpdate { replies }) => {
                eprintln!("[app:dbg] Replies: {:?}", &replies);
            }
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
            R2AMessage::Error(err) => {
                eprintln!("[app:dbg] Renderer error: {:?}", err);
            }
        }
    }
}
