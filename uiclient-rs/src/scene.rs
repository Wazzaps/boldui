use serde::Deserialize;
use skia_safe::{Color4f, Rect};
use std::collections::HashMap;
use std::fs::File;
use std::io::BufReader;

#[derive(Deserialize, Debug)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum ExprOp {
    Var {
        name: String,
    },
    Add {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Sub {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Mul {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Div {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Mod {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Pow {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Eq {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Neq {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Lt {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Lte {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Gt {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Gte {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    BAnd {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    BOr {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Not {
        a: Box<ExprPart>,
    },
    Neg {
        a: Box<ExprPart>,
    },
    BInvert {
        a: Box<ExprPart>,
    },
    Min {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Max {
        a: Box<ExprPart>,
        b: Box<ExprPart>,
    },
    Abs {
        a: Box<ExprPart>,
    },
    Inf,
    NegInf,
    ToStr {
        a: Box<ExprPart>,
    },
    #[serde(rename_all = "camelCase")]
    MeasureTextX {
        text: Box<ExprPart>,
        font_size: Box<ExprPart>,
    },
    #[serde(rename_all = "camelCase")]
    MeasureTextY {
        text: Box<ExprPart>,
        font_size: Box<ExprPart>,
    },
}

pub type EvalContext = HashMap<String, VarVal>;

#[derive(Debug, Clone)]
pub enum VarVal {
    Int(i64),
    Float(f64),
    String(String),
}

#[derive(Deserialize, Debug)]
#[serde(untagged)]
pub enum ExprPart {
    IntLiteral(i64),
    FloatLiteral(f64),
    StringLiteral(String),
    Operation(ExprOp),
}

impl ExprPart {
    pub fn as_f64(&self, ctx: &mut EvalContext) -> Result<f64, ()> {
        match self {
            ExprPart::IntLiteral(i) => Ok(*i as f64),
            ExprPart::FloatLiteral(f) => Ok(*f),
            ExprPart::Operation(op) => match op {
                ExprOp::Inf => Ok(f64::INFINITY),
                ExprOp::NegInf => Ok(f64::NEG_INFINITY),
                ExprOp::Var { name } => match ctx.get(name) {
                    Some(VarVal::Int(i)) => Ok(*i as f64),
                    Some(VarVal::Float(f)) => Ok(*f),
                    None => panic!("Missing variable '{}'", name),
                    _ => panic!("Invalid variable type of '{}'", name),
                },
                ExprOp::Add { a, b } => Ok(a.as_f64(ctx)? + b.as_f64(ctx)?),
                ExprOp::Sub { a, b } => Ok(a.as_f64(ctx)? - b.as_f64(ctx)?),
                ExprOp::Mul { a, b } => Ok(a.as_f64(ctx)? * b.as_f64(ctx)?),
                ExprOp::Div { a, b } => Ok(a.as_f64(ctx)? / b.as_f64(ctx)?),
                ExprOp::Mod { .. } => unimplemented!(),
                ExprOp::Pow { .. } => unimplemented!(),
                ExprOp::Eq { .. } => unimplemented!(),
                ExprOp::Neq { .. } => unimplemented!(),
                ExprOp::Lt { .. } => unimplemented!(),
                ExprOp::Lte { .. } => unimplemented!(),
                ExprOp::Gt { .. } => unimplemented!(),
                ExprOp::Gte { .. } => unimplemented!(),
                ExprOp::BAnd { .. } => unimplemented!(),
                ExprOp::BOr { .. } => unimplemented!(),
                ExprOp::BInvert { .. } => unimplemented!(),
                ExprOp::Not { .. } => unimplemented!(),
                ExprOp::Neg { .. } => unimplemented!(),
                ExprOp::Min { a, b } => Ok(a.as_f64(ctx)?.min(b.as_f64(ctx)?)),
                ExprOp::Max { a, b } => Ok(a.as_f64(ctx)?.max(b.as_f64(ctx)?)),
                ExprOp::Abs { a } => Ok(a.as_f64(ctx)?.abs()),
                ExprOp::ToStr { .. } => unimplemented!(),
                ExprOp::MeasureTextX { text, font_size } => {
                    let text = text.as_string(ctx).unwrap();
                    let font_size = font_size.as_f64(ctx)? as f32;
                    let font = crate::render::get_font("Cantarell", font_size);
                    let measurement =
                        crate::render::get_measurement(text.as_str(), &font, font_size);

                    Ok(measurement.0 as f64)
                }
                ExprOp::MeasureTextY { font_size, .. } => Ok(font_size.as_f64(ctx)?),
            },
            ExprPart::StringLiteral(_) => unimplemented!(),
        }
    }

    pub fn as_i64(&self, ctx: &mut EvalContext) -> Result<i64, ()> {
        match self {
            ExprPart::IntLiteral(i) => Ok(*i),
            ExprPart::FloatLiteral(f) => Ok(*f as i64),
            ExprPart::Operation(op) => match op {
                ExprOp::Inf => panic!("Cannot convert infinity to integer"),
                ExprOp::NegInf => panic!("Cannot convert -infinity to integer"),
                ExprOp::Var { name } => match ctx.get(name) {
                    Some(VarVal::Int(i)) => Ok(*i),
                    Some(VarVal::Float(f)) => Ok(*f as i64),
                    None => panic!("Missing variable '{}'", name),
                    _ => panic!("Invalid variable type"),
                },
                ExprOp::Add { a, b } => Ok(a.as_i64(ctx)? + b.as_i64(ctx)?),
                ExprOp::Sub { a, b } => Ok(a.as_i64(ctx)? - b.as_i64(ctx)?),
                ExprOp::Mul { a, b } => Ok(a.as_i64(ctx)? * b.as_i64(ctx)?),
                ExprOp::Div { a, b } => Ok(a.as_i64(ctx)? / b.as_i64(ctx)?),
                ExprOp::Mod { .. } => unimplemented!(),
                ExprOp::Pow { .. } => unimplemented!(),
                ExprOp::Eq { .. } => unimplemented!(),
                ExprOp::Neq { .. } => unimplemented!(),
                ExprOp::Lt { .. } => unimplemented!(),
                ExprOp::Lte { .. } => unimplemented!(),
                ExprOp::Gt { .. } => unimplemented!(),
                ExprOp::Gte { .. } => unimplemented!(),
                ExprOp::BAnd { a, b } => Ok(a.as_i64(ctx)? & b.as_i64(ctx)?),
                ExprOp::BOr { a, b } => Ok(a.as_i64(ctx)? | b.as_i64(ctx)?),
                ExprOp::BInvert { .. } => unimplemented!(),
                ExprOp::Not { .. } => unimplemented!(),
                ExprOp::Neg { .. } => unimplemented!(),
                ExprOp::Min { .. } => unimplemented!(),
                ExprOp::Max { .. } => unimplemented!(),
                ExprOp::Abs { a } => Ok(a.as_i64(ctx)?.abs()),
                ExprOp::ToStr { .. } => unimplemented!(),
                ExprOp::MeasureTextX { .. } => unimplemented!(),
                ExprOp::MeasureTextY { .. } => unimplemented!(),
            },
            ExprPart::StringLiteral(_) => unimplemented!(),
        }
    }

    pub fn as_color4f(&self, ctx: &mut EvalContext) -> Result<Color4f, ()> {
        Ok(Color4f::from(self.as_i64(ctx)? as u32))
    }

    pub fn as_string(&self, ctx: &mut EvalContext) -> Result<String, ()> {
        match self {
            ExprPart::StringLiteral(s) => Ok(s.clone()),
            ExprPart::Operation(op) => match op {
                ExprOp::Var { name } => match ctx.get(name) {
                    Some(VarVal::String(s)) => Ok(s.clone()),
                    None => panic!("Missing variable '{}'", name),
                    _ => panic!("Invalid variable type"),
                },
                ExprOp::ToStr { a } => Ok(format!("{}", a.as_f64(ctx)?)),
                ExprOp::Add { .. } => unimplemented!(),
                ExprOp::Sub { .. } => unimplemented!(),
                ExprOp::Mul { .. } => unimplemented!(),
                ExprOp::Div { .. } => unimplemented!(),
                ExprOp::Mod { .. } => unimplemented!(),
                ExprOp::Pow { .. } => unimplemented!(),
                ExprOp::Eq { .. } => unimplemented!(),
                ExprOp::Neq { .. } => unimplemented!(),
                ExprOp::Lt { .. } => unimplemented!(),
                ExprOp::Lte { .. } => unimplemented!(),
                ExprOp::Gt { .. } => unimplemented!(),
                ExprOp::Gte { .. } => unimplemented!(),
                ExprOp::BAnd { .. } => unimplemented!(),
                ExprOp::BInvert { .. } => unimplemented!(),
                ExprOp::BOr { .. } => unimplemented!(),
                ExprOp::Not { .. } => unimplemented!(),
                ExprOp::Neg { .. } => unimplemented!(),
                ExprOp::Min { .. } => unimplemented!(),
                ExprOp::Max { .. } => unimplemented!(),
                ExprOp::Abs { .. } => unimplemented!(),
                ExprOp::Inf => unimplemented!(),
                ExprOp::NegInf => unimplemented!(),
                ExprOp::MeasureTextX { .. } => unimplemented!(),
                ExprOp::MeasureTextY { .. } => unimplemented!(),
            },
            ExprPart::IntLiteral(_) => unimplemented!(),
            ExprPart::FloatLiteral(_) => unimplemented!(),
        }
    }
}

#[derive(Deserialize, Debug)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum HandlerOpcode {
    SetVar { name: String, value: Box<ExprPart> },
    Reply { id: u64, data: Vec<Box<ExprPart>> },
}

#[derive(Deserialize, Debug)]
#[serde(from = "ExprRectTuple")]
pub struct ExprRect {
    pub left: Box<ExprPart>,
    pub top: Box<ExprPart>,
    pub right: Box<ExprPart>,
    pub bottom: Box<ExprPart>,
}

impl ExprRect {
    pub fn as_rect(&self, ctx: &mut EvalContext) -> Result<Rect, ()> {
        Ok(Rect::new(
            self.left.as_f64(ctx)? as f32,
            self.top.as_f64(ctx)? as f32,
            self.right.as_f64(ctx)? as f32,
            self.bottom.as_f64(ctx)? as f32,
        ))
    }
}

#[derive(Deserialize, Debug)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum TopLevelOpcode {
    Clear {
        color: Box<ExprPart>,
    },
    Rect {
        rect: ExprRect,
        color: Box<ExprPart>,
    },
    #[serde(rename = "rrect")]
    RRect {
        rect: ExprRect,
        color: Box<ExprPart>,
        radius: Box<ExprPart>,
    },
    #[serde(rename = "evtHnd")]
    EventHandler {
        rect: ExprRect,
        events: u32,
        handler: Vec<HandlerOpcode>,
    },
    #[serde(rename_all = "camelCase")]
    Text {
        text: Box<ExprPart>,
        x: Box<ExprPart>,
        y: Box<ExprPart>,
        font_size: Box<ExprPart>,
        color: Box<ExprPart>,
    },
    Save {},
    Restore {},
    ClipRect {
        rect: ExprRect,
    },
    #[serde(rename_all = "camelCase")]
    Watch {
        id: u64,
        cond: Box<ExprPart>,
        wait_for_roundtrip: bool,
        handler: Vec<HandlerOpcode>,
    },
}

type ExprRectTuple = (Box<ExprPart>, Box<ExprPart>, Box<ExprPart>, Box<ExprPart>);

impl From<(Box<ExprPart>, Box<ExprPart>, Box<ExprPart>, Box<ExprPart>)> for ExprRect {
    fn from(rect: (Box<ExprPart>, Box<ExprPart>, Box<ExprPart>, Box<ExprPart>)) -> Self {
        ExprRect {
            left: rect.0,
            top: rect.1,
            right: rect.2,
            bottom: rect.3,
        }
    }
}

pub fn load_example_scene() -> Vec<TopLevelOpcode> {
    let mut args = std::env::args().skip(1);
    if args.len() != 1 {
        println!("Usage: uiclient <filename>");
        std::process::exit(1);
    }

    let filename = args.next().unwrap();
    let scene_file = File::open(filename).unwrap();
    let scene_reader = BufReader::new(scene_file);
    let scene: Vec<TopLevelOpcode> =
        serde_json::from_reader(scene_reader).expect("Failed to parse scene file");
    scene
}
