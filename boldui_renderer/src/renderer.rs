use crate::StateMachine;
use boldui_protocol::{CmdsCommand, Color, Value};
use skia_safe::{
    Canvas, Color4f, ColorSpace, Font, FontStyle, Paint, Point, Rect, TextBlob, TextEncoding,
    Typeface,
};

pub trait IntoColor4f {
    fn into_color4f(self) -> Color4f;
}

impl IntoColor4f for Color {
    fn into_color4f(self) -> Color4f {
        Color4f {
            r: self.r as f32 / u16::MAX as f32,
            g: self.g as f32 / u16::MAX as f32,
            b: self.b as f32 / u16::MAX as f32,
            a: self.a as f32 / u16::MAX as f32,
        }
    }
}

pub(crate) struct Renderer {}

impl Renderer {
    pub fn render(&mut self, canvas: &mut Canvas, state: &mut StateMachine) {
        let color_space = ColorSpace::new_srgb();
        // let img_size = canvas.base_layer_size();
        let root_scene = match state.root_scene {
            None => {
                canvas.clear(Color4f::new(0.5, 0.1, 0.1, 1.0));
                return;
            }
            Some(root_scene) => root_scene,
        };

        let (scene_desc, _scene_state) = state.scenes.get(&root_scene).unwrap();
        for cmd in scene_desc.cmds.iter() {
            match cmd {
                CmdsCommand::Clear { color } => {
                    let color = state.op_results.get(*color, (0, &[]));
                    let color = match color {
                        Value::Color(c) => c,
                        _ => panic!("Invalid type for 'color' param of 'Clear' cmd"),
                    };

                    canvas.clear(color.into_color4f());
                }
                CmdsCommand::DrawRect { paint, rect } => {
                    let paint = state.op_results.get(*paint, (0, &[]));
                    let paint = match paint {
                        Value::Color(c) => c,
                        _ => panic!("Invalid type for 'paint' param of 'DrawRect' cmd"),
                    };

                    let rect = state.op_results.get(*rect, (0, &[]));
                    let (left, top, right, bottom) = match rect {
                        Value::Rect {
                            left,
                            top,
                            right,
                            bottom,
                        } => (left, top, right, bottom),
                        _ => panic!("Invalid type for 'rect' param of 'DrawRect' cmd"),
                    };

                    canvas.draw_rect(
                        Rect::new(*left as f32, *top as f32, *right as f32, *bottom as f32),
                        &Paint::new(paint.into_color4f(), &color_space),
                    );
                }
                CmdsCommand::DrawCenteredText {
                    text,
                    paint,
                    center,
                } => {
                    let text = state.op_results.get(*text, (0, &[]));
                    let text = match text {
                        Value::String(s) => s,
                        _ => panic!("Invalid type for 'text' param of 'DrawCenteredText' cmd"),
                    };

                    if !text.is_empty() {
                        let paint = state.op_results.get(*paint, (0, &[]));
                        let paint = match paint {
                            Value::Color(c) => c,
                            _ => panic!("Invalid type for 'paint' param of 'DrawCenteredText' cmd"),
                        };

                        let center = state.op_results.get(*center, (0, &[]));
                        let (left, top) = match center {
                            Value::Point { left, top } => (left, top),
                            _ => {
                                panic!("Invalid type for 'center' param of 'DrawCenteredText' cmd")
                            }
                        };

                        const FONT_SIZE: f32 = 16.0;
                        const FONT_RECT_DBG: bool = false;

                        let paint = Paint::new(paint.into_color4f(), &color_space);
                        let typeface = Typeface::new("Heebo", FontStyle::default()).unwrap();
                        let font = Font::from_typeface(typeface, Some(FONT_SIZE));
                        let width = font.measure_str(text, Some(&paint)).0;
                        let text = TextBlob::from_str(text, &font).unwrap();

                        let left = *left as f32 - width / 2.0;
                        let top = *top as f32 + FONT_SIZE / 2.0;

                        if FONT_RECT_DBG {
                            canvas.draw_rect(
                                Rect::new(left, top - FONT_SIZE, left + width, top),
                                &Paint::new(Color::from_hex(0xaa0000).into_color4f(), &color_space),
                            );
                        }

                        canvas.draw_text_blob(text, Point::new(left, top), &paint);
                    }
                }
            }
        }
    }
}
