use crate::op_interpreter::OpResults;
use crate::state_machine::{SceneReplacement, SceneState};
use crate::StateMachine;
use boldui_protocol::{A2RUpdateScene, CmdsCommand, Color, SceneId, Value};
use skia_bindings::{GrSurfaceOrigin, SkAlphaType};
use skia_safe::gpu::BackendTexture;
use skia_safe::{
    Canvas, Color4f, ColorSpace, ColorType, Font, FontStyle, Image, Paint, Point, Rect, TextBlob,
    Typeface,
};
use std::collections::HashMap;

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

#[derive(Default)]
struct TypefaceCache {
    cache: HashMap<String, Typeface>,
}

impl TypefaceCache {
    // FIXME: use font style in cache
    pub fn get(&mut self, family_name: impl Into<String>, _font_style: FontStyle) -> &Typeface {
        let family_name = family_name.into();
        self.cache
            .entry(family_name.clone())
            .or_insert_with(|| Typeface::new(family_name, FontStyle::default()).unwrap())
    }
}

pub(crate) struct Renderer {
    typeface_cache: TypefaceCache,
    remote_texture: Option<BackendTexture>,
}

impl Renderer {
    pub fn new() -> Self {
        Self {
            typeface_cache: TypefaceCache::default(),
            remote_texture: None,
        }
    }

    fn render_scene_normally(
        canvas: &mut Canvas,
        color_space: ColorSpace,
        scene_desc: &A2RUpdateScene,
        typeface_cache: &mut TypefaceCache,
        op_results: &OpResults,
    ) {
        for cmd in scene_desc.cmds.iter() {
            match cmd {
                CmdsCommand::Clear { color } => {
                    let color = op_results.get(*color, (0, &[]));
                    let color = match color {
                        Value::Color(c) => c,
                        _ => panic!("Invalid type for 'color' param of 'Clear' cmd"),
                    };

                    canvas.clear(color.into_color4f());
                }
                CmdsCommand::DrawRect { paint, rect } => {
                    let paint = op_results.get(*paint, (0, &[]));
                    let paint = match paint {
                        Value::Color(c) => c,
                        _ => panic!("Invalid type for 'paint' param of 'DrawRect' cmd"),
                    };

                    let rect = op_results.get(*rect, (0, &[]));
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
                    let text = op_results.get(*text, (0, &[]));
                    let text = match text {
                        Value::String(s) => s,
                        _ => panic!("Invalid type for 'text' param of 'DrawCenteredText' cmd"),
                    };

                    if !text.is_empty() {
                        let paint = op_results.get(*paint, (0, &[]));
                        let paint = match paint {
                            Value::Color(c) => c,
                            _ => panic!("Invalid type for 'paint' param of 'DrawCenteredText' cmd"),
                        };

                        let center = op_results.get(*center, (0, &[]));
                        let (left, top) = match center {
                            Value::Point { left, top } => (left, top),
                            _ => {
                                panic!("Invalid type for 'center' param of 'DrawCenteredText' cmd")
                            }
                        };

                        const FONT_SIZE: f32 = 16.0;
                        const FONT_RECT_DBG: bool = false;

                        let paint = Paint::new(paint.into_color4f(), &color_space);
                        let typeface = typeface_cache.get("Cantarell", FontStyle::default());
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

    pub fn render_scene(
        &mut self,
        canvas: &mut Canvas,
        state: &mut StateMachine,
        root_scene: SceneId,
    ) {
        // if !self.did_remote_connect {
        //     ;
        //     self.did_remote_connect = true;
        // }
        let color_space = ColorSpace::new_srgb();
        // let img_size = canvas.base_layer_size();
        // canvas
        //     .surface()
        //     .unwrap()
        //     .get_backend_texture()
        //     .unwrap()
        //     .unwrap();

        // let remote_texture = self
        //     .remote_texture
        //     .get_or_insert_with(|| crate::dmabuf::connect_to_remote_texture());
        // let remote_img = Image::from_texture(
        //     &mut canvas.recording_context().unwrap(),
        //     remote_texture,
        //     GrSurfaceOrigin::TopLeft,
        //     ColorType::RGBA8888,
        //     SkAlphaType::Opaque,
        //     Some(color_space.clone()),
        // )
        // .unwrap();

        let (scene_desc, scene_state) = state.scenes.get_mut(&root_scene).unwrap();
        if scene_state.scene_replacement.is_pending() {
            scene_state
                .scene_replacement
                .realise_pending_external_widget();
        }

        match &scene_state.scene_replacement {
            SceneReplacement::None => {
                Self::render_scene_normally(
                    canvas,
                    color_space,
                    scene_desc,
                    &mut self.typeface_cache,
                    &state.op_results,
                );
            }
            SceneReplacement::PendingExternalWidget { .. } => unreachable!(),
            SceneReplacement::ExternalWidget { texture } => {
                let remote_img = Image::from_texture(
                    &mut canvas.recording_context().unwrap(),
                    texture,
                    GrSurfaceOrigin::TopLeft,
                    ColorType::RGBA8888,
                    SkAlphaType::Opaque,
                    Some(color_space.clone()),
                )
                .unwrap();
                canvas.draw_image(&remote_img, Point::new(0.0, 0.0), None);
            }
        }
    }
}
