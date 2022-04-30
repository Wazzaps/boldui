use crate::scene::{
    eval_oplist, load_example_scene, EvalContext, ExprPart, HandlerOpcode, Scene, TopLevelOpcode,
    VarVal,
};
use glutin::dpi::PhysicalPosition;
use lazy_static::lazy_static;
use skia_safe::{Canvas, Color, Color4f, Contains, FontStyle, Paint, Point, RRect, Rect, TextBlob};
use std::collections::HashMap;

use std::sync::{Arc, Mutex};
use std::time::Instant;

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

struct EventHandler {
    rect: Rect,
    events: u32,
    handler: Vec<HandlerOpcode>,
    oplist: Vec<ExprPart>,
}

pub struct UIClient {
    pub scene: Scene,
    event_handlers: Vec<EventHandler>,
    last_size: (i32, i32),
    variables: EvalContext,
    start_time: Instant,
}

fn make_paint(color: Color4f) -> Paint {
    let mut paint = Paint::default();
    paint.set_anti_alias(true);
    paint.set_color(color.to_color());
    paint
}

impl UIClient {
    pub fn new() -> UIClient {
        let mut ctx = EvalContext::new();
        ctx.insert("counter".to_string(), VarVal::Int(0));
        ctx.insert(
            "__client_version".to_string(),
            VarVal::String(concat!("BoldUI Client v", env!("CARGO_PKG_VERSION")).to_string()),
        );

        UIClient {
            scene: load_example_scene(),
            event_handlers: Vec::new(),
            last_size: (0, 0),
            variables: ctx,
            start_time: Instant::now(),
        }
    }

    pub fn draw(&mut self, canvas: &mut Canvas, width: i32, height: i32) {
        self.last_size = (width, height);

        let mut ctx = self.variables.clone();
        ctx.insert("width".to_string(), VarVal::Int(width as i64));
        ctx.insert("height".to_string(), VarVal::Int(height as i64));
        ctx.insert(
            "time".to_string(),
            VarVal::Float(Instant::now().duration_since(self.start_time).as_secs_f64()),
        );
        ctx.insert("lv1_lv_list_start".to_string(), VarVal::Float(0.0));
        ctx.insert("lv1_lv_scroll_pos".to_string(), VarVal::Float(0.0));
        ctx.insert("d:Model#0".to_string(), VarVal::Int(123));

        let mut new_event_handlers = Vec::new();

        let op_results = self.scene.eval_oplist(&ctx).unwrap();
        canvas.clear(Color::BLACK);
        for opcode in &self.scene.scene {
            match opcode {
                TopLevelOpcode::Clear { color } => {
                    canvas.clear(Color4f::from(*color));
                }
                TopLevelOpcode::Rect { rect, color } => {
                    canvas.draw_rect(
                        rect.as_rect(&op_results).unwrap(),
                        &make_paint(op_results[*color].as_color4f().unwrap()),
                    );
                }
                TopLevelOpcode::RRect {
                    rect,
                    color,
                    radius,
                } => {
                    let rad = op_results[*radius].as_float().unwrap() as f32;
                    canvas.draw_rrect(
                        RRect::new_rect_xy(rect.as_rect(&op_results).unwrap(), rad, rad),
                        &make_paint(op_results[*color].as_color4f().unwrap()),
                    );
                }
                TopLevelOpcode::Text {
                    text,
                    x,
                    y,
                    font_size,
                    color,
                } => {
                    let text = op_results[*text].as_string().unwrap();
                    let x = op_results[*x].as_float().unwrap() as f32;
                    let y = op_results[*y].as_float().unwrap() as f32;
                    let font_size = op_results[*font_size].as_float().unwrap() as f32;
                    let color = op_results[*color].as_color4f().unwrap();

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
                TopLevelOpcode::Save { .. } => {}
                TopLevelOpcode::Restore { .. } => {}
                TopLevelOpcode::ClipRect { .. } => {}
                TopLevelOpcode::Watch { .. } => {}
                TopLevelOpcode::EventHandler {
                    rect,
                    events,
                    handler,
                    oplist,
                } => {
                    let rect = rect.as_rect(&op_results).unwrap();
                    new_event_handlers.push(EventHandler {
                        rect,
                        events: *events,
                        handler: (*handler).clone(),
                        oplist: (*oplist).clone(),
                    });
                }
            }
        }

        self.event_handlers = new_event_handlers;
    }

    fn _eval_handlers(
        variables: &mut EvalContext,
        handlers: &[HandlerOpcode],
        op_results: &[VarVal],
    ) {
        for handler in handlers {
            match handler {
                HandlerOpcode::SetVar { name, value } => {
                    println!("Setting var {} to {:?}", name, &op_results[*value]);
                    variables.insert(name.to_string(), op_results[*value].clone());
                }
                HandlerOpcode::Reply { id, data } => {
                    print!("UNIMPL: Would send: id={}, ", id);
                    for d in data {
                        let value = &op_results[*d];
                        print!("{:?}, ", value);
                    }
                    println!();
                }
            }
        }
    }

    pub fn handle_mouse_down<F>(&mut self, position: PhysicalPosition<f64>, redraw_cb: F)
    where
        F: Fn(),
    {
        println!("mouse down at {} {}", position.x, position.y);
        let mut redraw = false;

        for handler in &self.event_handlers {
            if handler.events & (1 << 0) != 0
                && handler
                    .rect
                    .contains(Point::new(position.x as f32, position.y as f32))
            {
                let mut ctx = self.variables.clone();
                ctx.insert("width".to_string(), VarVal::Int(self.last_size.0 as i64));
                ctx.insert("height".to_string(), VarVal::Int(self.last_size.1 as i64));
                ctx.insert("event_x".to_string(), VarVal::Float(position.x));
                ctx.insert("event_y".to_string(), VarVal::Float(position.y));
                ctx.insert(
                    "time".to_string(),
                    VarVal::Float(Instant::now().duration_since(self.start_time).as_secs_f64()),
                );

                let op_results = eval_oplist(&handler.oplist, &ctx).unwrap();
                UIClient::_eval_handlers(&mut self.variables, &handler.handler, &op_results);
                redraw = true;
            }
        }

        if redraw {
            redraw_cb();
        }
    }
}
