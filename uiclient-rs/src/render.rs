use crate::scene::{load_example_scene, EvalContext, TopLevelOpcode, VarVal};
use lazy_static::lazy_static;
use skia_safe::{Canvas, Color, Color4f, FontStyle, Paint, Point, RRect, Rect, TextBlob};
use std::collections::HashMap;
use std::convert::TryInto;
use std::sync::{Arc, Mutex};

#[derive(PartialEq, Eq, Hash, Debug)]
struct MeasurementKey(String, u32, String);

#[derive(PartialEq, Eq, Hash, Debug)]
struct FontKey(String, u32);

lazy_static! {
    static ref TEXT_MEASUREMENT_CACHE: Mutex<HashMap<MeasurementKey, (f32, f32)>> =
        Mutex::new(HashMap::new());
    static ref FONT_CACHE: Mutex<HashMap<FontKey, Arc<skia_safe::Font>>> =
        Mutex::new(HashMap::new());
}

pub fn get_measurement(text: &str, font: &skia_safe::Font, font_size: f32) -> (f32, f32) {
    let mut cache = TEXT_MEASUREMENT_CACHE.lock().unwrap();
    let key = MeasurementKey(
        font.typeface().unwrap().family_name(),
        (font_size * 100.0).round() as u32,
        text.to_string(),
    );

    match cache.get(&key) {
        None => {
            let width = font.measure_str(text, None).0;
            let dimensions = (width, font_size);
            cache.insert(key, dimensions);
            dimensions
        }
        Some(dimensions) => *dimensions,
    }
}

pub fn get_font(family_name: &str, font_size: f32) -> Arc<skia_safe::Font> {
    let mut font_cache = FONT_CACHE.lock().unwrap();
    let key = FontKey(family_name.to_string(), (font_size * 100.0).round() as u32);

    match font_cache.get(&key) {
        None => {
            let font = Arc::new(skia_safe::Font::new(
                skia_safe::Typeface::new("Cantarell", FontStyle::default()).unwrap(),
                font_size,
            ));
            font_cache.insert(key, font.clone());
            font
        }
        Some(font) => font.clone(),
    }
}

pub struct UIClient {
    scene: Vec<TopLevelOpcode>,
}

fn make_paint(color: Color4f) -> Paint {
    let mut paint = Paint::default();
    paint.set_anti_alias(true);
    paint.set_color(color.to_color());
    paint
}

impl UIClient {
    pub fn new() -> UIClient {
        UIClient {
            scene: load_example_scene(),
        }
    }

    pub fn draw(&self, canvas: &mut Canvas, width: i32, height: i32) {
        let mut ctx = EvalContext::new();
        ctx.insert("width".to_string(), VarVal::Int(width as i64));
        ctx.insert("height".to_string(), VarVal::Int(height as i64));
        ctx.insert("counter".to_string(), VarVal::Int(1234));

        canvas.clear(Color::BLACK);
        for opcode in &self.scene {
            match opcode {
                TopLevelOpcode::Clear { color } => {
                    canvas.clear(color.as_color4f(&mut ctx).unwrap());
                }
                TopLevelOpcode::Rect { rect, color } => {
                    canvas.draw_rect(
                        rect.as_rect(&mut ctx).unwrap(),
                        &make_paint(color.as_color4f(&mut ctx).unwrap()),
                    );
                }
                TopLevelOpcode::RRect {
                    rect,
                    color,
                    radius,
                } => {
                    let rad = radius.as_f64(&mut ctx).unwrap() as f32;
                    canvas.draw_rrect(
                        RRect::new_rect_xy(rect.as_rect(&mut ctx).unwrap(), rad, rad),
                        &make_paint(color.as_color4f(&mut ctx).unwrap()),
                    );
                }
                TopLevelOpcode::EventHandler { .. } => {}
                TopLevelOpcode::Text {
                    text,
                    x,
                    y,
                    font_size,
                    color,
                } => {
                    let text = text.as_string(&mut ctx).unwrap();
                    let x = x.as_f64(&mut ctx).unwrap() as f32;
                    let y = y.as_f64(&mut ctx).unwrap() as f32;
                    let font_size = font_size.as_f64(&mut ctx).unwrap() as f32;
                    let color = color.as_color4f(&mut ctx).unwrap();

                    let font = get_font("Cantarell", font_size);
                    let measurement = get_measurement(text.as_str(), &font, font_size);
                    let text_blob = TextBlob::new(text.as_str(), &font).unwrap();
                    canvas.draw_text_blob(
                        text_blob,
                        Point::new(
                            x - (measurement.0 / 2.0).floor(),
                            y + (measurement.1 / 2.0).floor(),
                        ),
                        &make_paint(color),
                    );
                }
            }
        }
        // canvas.draw_text(0, 0, "Hello, world!");
    }
}
