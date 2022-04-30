use crate::render::{get_font, get_measurement};
use crate::utils::{fmod, imod};
use serde::Deserialize;
use skia_safe::{Color4f, Rect};
use std::collections::HashMap;
use std::fs::File;
use std::io::BufReader;

#[derive(Deserialize, Debug, Clone)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum ExprOp {
    Var {
        name: String,
    },
    Add {
        a: usize,
        b: usize,
    },
    Sub {
        a: usize,
        b: usize,
    },
    Mul {
        a: usize,
        b: usize,
    },
    Div {
        a: usize,
        b: usize,
    },
    Fdiv {
        a: usize,
        b: usize,
    },
    Mod {
        a: usize,
        b: usize,
    },
    Pow {
        a: usize,
        b: usize,
    },
    Eq {
        a: usize,
        b: usize,
    },
    Neq {
        a: usize,
        b: usize,
    },
    Lt {
        a: usize,
        b: usize,
    },
    Lte {
        a: usize,
        b: usize,
    },
    Gt {
        a: usize,
        b: usize,
    },
    Gte {
        a: usize,
        b: usize,
    },
    BAnd {
        a: usize,
        b: usize,
    },
    BOr {
        a: usize,
        b: usize,
    },
    Not {
        a: usize,
    },
    Neg {
        a: usize,
    },
    BInvert {
        a: usize,
    },
    Min {
        a: usize,
        b: usize,
    },
    Max {
        a: usize,
        b: usize,
    },
    Abs {
        a: usize,
    },
    Inf,
    ToStr {
        a: usize,
    },
    #[serde(rename_all = "camelCase")]
    MeasureTextX {
        text: usize,
        font_size: usize,
    },
    #[serde(rename_all = "camelCase")]
    MeasureTextY {
        text: usize,
        font_size: usize,
    },
    If {
        cond: usize,
        t: usize,
        f: usize,
    },
}

pub type EvalContext = HashMap<String, VarVal>;

#[derive(Debug, Clone)]
pub enum VarVal {
    Null,
    Int(i64),
    Float(f64),
    String(String),
}

impl VarVal {
    pub fn as_int(&self) -> Option<i64> {
        match self {
            VarVal::Int(i) => Some(*i),
            VarVal::Float(f) => Some((*f) as i64),
            _ => None,
        }
    }

    pub fn as_float(&self) -> Option<f64> {
        match self {
            VarVal::Float(f) => Some(*f),
            VarVal::Int(i) => Some((*i) as f64),
            _ => None,
        }
    }

    pub fn as_string(&self) -> Option<String> {
        match self {
            VarVal::String(s) => Some(s.clone()),
            VarVal::Int(i) => Some(i.to_string()),
            VarVal::Float(f) => Some(f.to_string()),
            _ => None,
        }
    }

    pub fn as_color4f(&self) -> Option<Color4f> {
        match self {
            VarVal::Int(i) => Some(Color4f::from(*i as u32)),
            _ => None,
        }
    }
}

#[derive(Deserialize, Debug, Clone)]
#[serde(untagged)]
pub enum ExprPart {
    IntLiteral(i64),
    FloatLiteral(f64),
    StringLiteral(String),
    Operation(ExprOp),
}

impl ExprPart {
    pub fn eval(&self, ctx: &EvalContext, op_results: &[VarVal]) -> Result<VarVal, ()> {
        match self {
            ExprPart::StringLiteral(s) => Ok(VarVal::String(s.clone())),
            ExprPart::IntLiteral(i) => Ok(VarVal::Int(*i)),
            ExprPart::FloatLiteral(f) => Ok(VarVal::Float(*f)),
            ExprPart::Operation(op) => match op {
                ExprOp::Var { name } => match ctx.get(name) {
                    Some(v) => Ok(v.clone()),
                    None => panic!("Missing variable '{}'", name),
                },
                ExprOp::Add { a, b } => match (&op_results[*a], &op_results[*b]) {
                    (VarVal::Int(a), VarVal::Int(b)) => Ok(VarVal::Int(*a + *b)),
                    (VarVal::Int(a), VarVal::Float(b)) => Ok(VarVal::Float(*a as f64 + *b)),
                    (VarVal::Float(a), VarVal::Int(b)) => Ok(VarVal::Float(*a + *b as f64)),
                    (VarVal::Float(a), VarVal::Float(b)) => Ok(VarVal::Float(*a + *b)),
                    (VarVal::Null, _) => Ok(VarVal::Null),
                    (_, VarVal::Null) => Ok(VarVal::Null),
                    _ => panic!("Invalid operands for addition"),
                },
                ExprOp::Mul { a, b } => match (&op_results[*a], &op_results[*b]) {
                    (VarVal::Int(a), VarVal::Int(b)) => {
                        Ok(VarVal::Int((*a as f64 * *b as f64) as i64))
                    }
                    (VarVal::Int(a), VarVal::Float(b)) => Ok(VarVal::Int((*a as f64 * *b) as i64)),
                    (VarVal::Float(a), VarVal::Int(b)) => Ok(VarVal::Int((*a * *b as f64) as i64)),
                    (VarVal::Float(a), VarVal::Float(b)) => Ok(VarVal::Int((*a * *b) as i64)),
                    (VarVal::Null, _) => Ok(VarVal::Null),
                    (_, VarVal::Null) => Ok(VarVal::Null),
                    _ => panic!("Invalid operands for multiply"),
                },
                ExprOp::Fdiv { a, b } => match (&op_results[*a], &op_results[*b]) {
                    (VarVal::Int(a), VarVal::Int(b)) => {
                        Ok(VarVal::Int((*a as f64 / *b as f64) as i64))
                    }
                    (VarVal::Int(a), VarVal::Float(b)) => Ok(VarVal::Int((*a as f64 / *b) as i64)),
                    (VarVal::Float(a), VarVal::Int(b)) => Ok(VarVal::Int((*a / *b as f64) as i64)),
                    (VarVal::Float(a), VarVal::Float(b)) => Ok(VarVal::Int((*a / *b) as i64)),
                    (VarVal::Null, _) => Ok(VarVal::Null),
                    (_, VarVal::Null) => Ok(VarVal::Null),
                    _ => panic!("Invalid operands for floor-division"),
                },
                ExprOp::Div { a, b } => match (&op_results[*a], &op_results[*b]) {
                    (VarVal::Int(a), VarVal::Int(b)) => Ok(VarVal::Float(*a as f64 / *b as f64)),
                    (VarVal::Int(a), VarVal::Float(b)) => Ok(VarVal::Float(*a as f64 / *b)),
                    (VarVal::Float(a), VarVal::Int(b)) => Ok(VarVal::Float(*a / *b as f64)),
                    (VarVal::Float(a), VarVal::Float(b)) => Ok(VarVal::Float(*a / *b)),
                    (VarVal::Null, _) => Ok(VarVal::Null),
                    (_, VarVal::Null) => Ok(VarVal::Null),
                    _ => panic!("Invalid operands for division"),
                },
                ExprOp::Gt { a, b } => match (&op_results[*a], &op_results[*b]) {
                    (VarVal::Int(a), VarVal::Int(b)) => {
                        Ok(VarVal::Int(if *a > *b { 1 } else { 0 }))
                    }
                    (VarVal::Int(a), VarVal::Float(b)) => {
                        Ok(VarVal::Int(if *a as f64 > *b { 1 } else { 0 }))
                    }
                    (VarVal::Float(a), VarVal::Int(b)) => {
                        Ok(VarVal::Int(if *a > *b as f64 { 1 } else { 0 }))
                    }
                    (VarVal::Float(a), VarVal::Float(b)) => {
                        Ok(VarVal::Int(if *a > *b { 1 } else { 0 }))
                    }
                    (VarVal::Null, _) => Ok(VarVal::Null),
                    (_, VarVal::Null) => Ok(VarVal::Null),
                    _ => panic!("Invalid operands for greater-than"),
                },
                ExprOp::Abs { a } => match &op_results[*a] {
                    VarVal::Int(a) => Ok(VarVal::Int(a.abs())),
                    VarVal::Float(a) => Ok(VarVal::Float(a.abs())),
                    VarVal::Null => Ok(VarVal::Null),
                    _ => panic!("Invalid operands for abs"),
                },
                ExprOp::If { cond, t, f } => match &op_results[*cond] {
                    VarVal::Int(1) => Ok(op_results[*t].clone()),
                    _ => Ok(op_results[*f].clone()),
                },
                ExprOp::Eq { a, b } => match (&op_results[*a], &op_results[*b]) {
                    (VarVal::Int(a), VarVal::Int(b)) => Ok(VarVal::Int((*a == (*b as i64)) as i64)),
                    (VarVal::Int(a), VarVal::Float(b)) => {
                        Ok(VarVal::Int(((*a as f64) == *b) as i64))
                    }
                    (VarVal::Float(a), VarVal::Int(b)) => {
                        Ok(VarVal::Int((*a == (*b as f64)) as i64))
                    }
                    (VarVal::Float(a), VarVal::Float(b)) => Ok(VarVal::Int((*a == *b) as i64)),
                    (VarVal::String(a), VarVal::String(b)) => Ok(VarVal::Int((*a == *b) as i64)),
                    (VarVal::Null, _) => Ok(VarVal::Int(0)),
                    (_, VarVal::Null) => Ok(VarVal::Int(0)),
                    _ => panic!("Invalid operands for equality"),
                },
                ExprOp::Min { a, b } => match (&op_results[*a], &op_results[*b]) {
                    (VarVal::Int(a), VarVal::Int(b)) => Ok(VarVal::Int((*a).min(*b))),
                    (VarVal::Int(a), VarVal::Float(b)) => Ok(VarVal::Float((*a as f64).min(*b))),
                    (VarVal::Float(a), VarVal::Int(b)) => Ok(VarVal::Float((*a).min(*b as f64))),
                    (VarVal::Float(a), VarVal::Float(b)) => Ok(VarVal::Float((*a).min(*b))),
                    (VarVal::Null, _) => Ok(VarVal::Null),
                    (_, VarVal::Null) => Ok(VarVal::Null),
                    _ => panic!("Invalid operands for min"),
                },
                ExprOp::Max { a, b } => match (&op_results[*a], &op_results[*b]) {
                    (VarVal::Int(a), VarVal::Int(b)) => Ok(VarVal::Int((*a).max(*b))),
                    (VarVal::Int(a), VarVal::Float(b)) => Ok(VarVal::Float((*a as f64).max(*b))),
                    (VarVal::Float(a), VarVal::Int(b)) => Ok(VarVal::Float((*a).max(*b as f64))),
                    (VarVal::Float(a), VarVal::Float(b)) => Ok(VarVal::Float((*a).max(*b))),
                    (VarVal::Null, _) => Ok(VarVal::Null),
                    (_, VarVal::Null) => Ok(VarVal::Null),
                    _ => panic!("Invalid operands for max"),
                },
                ExprOp::Mod { a, b } => match (&op_results[*a], &op_results[*b]) {
                    (VarVal::Int(a), VarVal::Int(b)) => Ok(VarVal::Int(imod(*a, *b))),
                    (VarVal::Int(a), VarVal::Float(b)) => Ok(VarVal::Float(fmod(*a as f64, *b))),
                    (VarVal::Float(a), VarVal::Int(b)) => Ok(VarVal::Float(fmod(*a, *b as f64))),
                    (VarVal::Float(a), VarVal::Float(b)) => Ok(VarVal::Float(fmod(*a, *b))),
                    (VarVal::Null, _) => Ok(VarVal::Null),
                    (_, VarVal::Null) => Ok(VarVal::Null),
                    _ => panic!("Invalid operands for mod"),
                },
                ExprOp::Neg { a } => match &op_results[*a] {
                    VarVal::Int(a) => Ok(VarVal::Int(-*a)),
                    VarVal::Float(a) => Ok(VarVal::Float(-*a)),
                    VarVal::Null => Ok(VarVal::Null),
                    _ => panic!("Invalid operands for neg"),
                },
                ExprOp::MeasureTextX { text, font_size } => {
                    let text = op_results[*text].as_string().unwrap();
                    let font_size = op_results[*font_size].as_float().unwrap() as f32;

                    let font = get_font("Cantarell", font_size);
                    let measurement = get_measurement(text.as_str(), &font, font_size);

                    Ok(VarVal::Float(measurement.0 as f64))
                }
                ExprOp::MeasureTextY { text, font_size } => {
                    let text = op_results[*text].as_string().unwrap();
                    let font_size = op_results[*font_size].as_float().unwrap() as f32;

                    let font = get_font("Cantarell", font_size);
                    let measurement = get_measurement(text.as_str(), &font, font_size);

                    Ok(VarVal::Float(measurement.1 as f64))
                }
                _ => unimplemented!("{op:?}"),
            },
        }
    }
}

#[derive(Deserialize, Debug, Clone)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum HandlerOpcode {
    SetVar { name: String, value: usize },
    Reply { id: u64, data: Vec<usize> },
}

#[derive(Deserialize, Debug)]
#[serde(from = "ExprRectTuple")]
pub struct ExprRect {
    pub left: usize,
    pub top: usize,
    pub right: usize,
    pub bottom: usize,
}

impl ExprRect {
    pub fn as_rect(&self, op_results: &[VarVal]) -> Option<Rect> {
        Some(Rect::new(
            op_results[self.left].as_float()? as f32,
            op_results[self.top].as_float()? as f32,
            op_results[self.right].as_float()? as f32,
            op_results[self.bottom].as_float()? as f32,
        ))
    }
}

#[derive(Deserialize, Debug)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum TopLevelOpcode {
    Clear {
        color: u32,
    },
    Rect {
        rect: ExprRect,
        color: usize,
    },
    #[serde(rename = "rrect")]
    RRect {
        rect: ExprRect,
        color: usize,
        radius: usize,
    },
    #[serde(rename = "evtHnd")]
    EventHandler {
        rect: ExprRect,
        events: u32,
        handler: Vec<HandlerOpcode>,
        oplist: Vec<ExprPart>,
    },
    #[serde(rename_all = "camelCase")]
    Text {
        text: usize,
        x: usize,
        y: usize,
        font_size: usize,
        color: usize,
    },
    Save {},
    Restore {},
    ClipRect {
        rect: ExprRect,
    },
    #[serde(rename_all = "camelCase")]
    Watch {
        id: u64,
        cond: usize,
        wait_for_roundtrip: bool,
        handler: Vec<HandlerOpcode>,
    },
}

#[derive(Deserialize, Debug)]
pub struct Scene {
    oplist: Vec<ExprPart>,
    pub(crate) scene: Vec<TopLevelOpcode>,
}

pub fn eval_oplist(oplist: &[ExprPart], ctx: &EvalContext) -> Result<Vec<VarVal>, ()> {
    let mut op_results = Vec::new();
    for op in oplist {
        op_results.push(op.eval(ctx, &op_results)?);
    }
    Ok(op_results)
}

impl Scene {
    pub fn eval_oplist(&self, ctx: &EvalContext) -> Result<Vec<VarVal>, ()> {
        eval_oplist(&self.oplist, ctx)
    }
}

type ExprRectTuple = (usize, usize, usize, usize);

impl From<(usize, usize, usize, usize)> for ExprRect {
    fn from(rect: (usize, usize, usize, usize)) -> Self {
        ExprRect {
            left: rect.0,
            top: rect.1,
            right: rect.2,
            bottom: rect.3,
        }
    }
}

pub fn load_example_scene() -> Scene {
    let mut args = std::env::args().skip(1);
    if args.len() != 1 {
        println!("Usage: uiclient <filename>");
        std::process::exit(1);
    }

    let filename = args.next().unwrap();
    let scene_file = File::open(filename).unwrap();
    let scene_reader = BufReader::new(scene_file);
    let scene: Scene = serde_json::from_reader(scene_reader).expect("Failed to parse scene file");
    scene
}
