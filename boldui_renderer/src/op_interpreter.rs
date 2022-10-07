use crate::StateMachine;
use boldui_protocol::{OpId, OpsOperation, SceneId, Value, VarId};
use std::collections::HashMap;

#[derive(Debug)]
pub struct OpResults {
    pub vals: HashMap<SceneId, Vec<Value>>,
}

impl OpResults {
    pub fn new() -> Self {
        Self {
            vals: HashMap::new(),
        }
    }

    pub fn get<'a>(&'a self, id: OpId, ctx: (SceneId, &'a [Value])) -> &'a Value {
        if id.scene_id == ctx.0 {
            ctx.1.get(id.idx as usize).unwrap_or_else(|| {
                panic!(
                    "Scene #{} has no item id #{} (it has {} items)",
                    id.scene_id,
                    id.idx,
                    ctx.1.len()
                )
            })
        } else {
            self.vals
                .get(&id.scene_id)
                .unwrap()
                .get(id.idx as usize)
                .unwrap()
        }
    }

    pub fn get_f64<'a>(&'a self, id: OpId, ctx: (SceneId, &'a [Value])) -> f64 {
        match self.get(id, ctx) {
            Value::Sint64(i) => *i as f64,
            Value::Double(f) => *f,
            val => panic!("Tried to convert {:?} into float", val),
        }
    }

    pub fn get_point<'a>(&'a self, id: OpId, ctx: (SceneId, &'a [Value])) -> (f64, f64) {
        match self.get(id, ctx) {
            Value::Point { left, top } => (*left, *top),
            val => panic!("Tried to convert {:?} into Point", val),
        }
    }

    pub fn get_num_pair<'a>(
        &'a self,
        id_a: OpId,
        ctx_a: (SceneId, &'a [Value]),
        id_b: OpId,
        ctx_b: (SceneId, &'a [Value]),
    ) -> IntOrFloatPair {
        match (self.get(id_a, ctx_a), self.get(id_b, ctx_b)) {
            (Value::Sint64(a), Value::Sint64(b)) => IntOrFloatPair::Int(*a, *b),
            (Value::Sint64(a), Value::Double(b)) => IntOrFloatPair::Float(*a as f64, *b),
            (Value::Double(a), Value::Sint64(b)) => IntOrFloatPair::Float(*a, *b as f64),
            (Value::Double(a), Value::Double(b)) => IntOrFloatPair::Float(*a, *b),
            (a, b) => panic!(
                "Tried to get the following pair as numbers: ({:?}, {:?})",
                a, b
            ),
        }
    }
}

pub enum IntOrFloatPair {
    Int(i64, i64),
    Float(f64, f64),
}

impl StateMachine {
    pub fn eval_op(&self, op: &OpsOperation, ctx: (SceneId, &[Value])) -> Value {
        match op {
            OpsOperation::Value(val) => val.to_owned(),
            OpsOperation::Var(VarId { key, scene }) => self
                .scenes
                .get(scene)
                .unwrap()
                .1
                .var_vals
                .get(key)
                .unwrap()
                .to_owned(),
            OpsOperation::Add { a, b } => match self.op_results.get_num_pair(*a, ctx, *b, ctx) {
                IntOrFloatPair::Int(a, b) => Value::Sint64(a + b),
                IntOrFloatPair::Float(a, b) => Value::Double(a + b),
            },
            OpsOperation::Neg { a } => match self.op_results.get(*a, ctx) {
                Value::Sint64(val) => Value::Sint64(-*val),
                Value::Double(val) => Value::Double(-*val),
                val => panic!("Tried to convert {:?} into a number", val),
            },
            OpsOperation::Eq { a, b } => {
                match (self.op_results.get(*a, ctx), self.op_results.get(*b, ctx)) {
                    (Value::Sint64(a), Value::Sint64(b)) => Value::Sint64((a == b) as i64),
                    (Value::Double(a), Value::Double(b)) => Value::Sint64((a == b) as i64),
                    val => todo!("Unimpl type for eq: {:?}", val),
                }
            }
            OpsOperation::GetTime { .. } => {
                todo!()
            }
            OpsOperation::MakePoint { left, top } => Value::Point {
                left: self.op_results.get_f64(*left, ctx),
                top: self.op_results.get_f64(*top, ctx),
            },
            OpsOperation::MakeRectFromPoints {
                left_top,
                right_bottom,
            } => {
                let left_top = self.op_results.get_point(*left_top, ctx);
                let right_bottom = self.op_results.get_point(*right_bottom, ctx);
                Value::Rect {
                    left: left_top.0,
                    top: left_top.1,
                    right: right_bottom.0,
                    bottom: right_bottom.1,
                }
            }
            OpsOperation::MakeRectFromSides {
                left,
                top,
                right,
                bottom,
            } => Value::Rect {
                left: self.op_results.get_f64(*left, ctx),
                top: self.op_results.get_f64(*top, ctx),
                right: self.op_results.get_f64(*right, ctx),
                bottom: self.op_results.get_f64(*bottom, ctx),
            },
        }
    }
}
