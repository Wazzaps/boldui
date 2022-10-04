use crate::image_frontend::ImageEventLoopProxy;
use crate::SerdeSender;
use boldui_protocol::{
    bincode, A2RMessage, A2RReparentScene, A2RUpdate, A2RUpdateScene, HandlerCmd, OpId,
    OpsOperation, SceneId, Value, VarId,
};
use byteorder::{ReadBytesExt, LE};
use parking_lot::Mutex;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::io::{Read, Write};
use std::sync::{Arc, Barrier};

#[derive(Copy, Clone, Eq, PartialEq, Debug, Default)]
pub enum SceneParent {
    #[default]
    NoParent,
    Hidden,
    Root,
    Parent(SceneId),
}

impl SceneParent {
    pub fn has_parent(&self) -> bool {
        !matches!(self, SceneParent::NoParent)
    }

    pub fn unwrap(self) -> SceneId {
        match self {
            SceneParent::NoParent => panic!("called `SceneParent::unwrap()` on a `NoParent` value"),
            SceneParent::Hidden => panic!("called `SceneParent::unwrap()` on a `Hidden` value"),
            SceneParent::Root => panic!("called `SceneParent::unwrap()` on a `Root` value"),
            SceneParent::Parent(scene) => scene,
        }
    }
}

#[derive(Debug, Default)]
pub struct SceneState {
    pub children: Vec<SceneId>,
    pub parent: SceneParent,
    pub var_vals: BTreeMap<String, Value>,
}

pub type Scene = (A2RUpdateScene, SceneState);

#[derive(Debug)]
pub struct OpResults {
    pub vals: HashMap<SceneId, Vec<Value>>,
}

pub enum IntOrFloatPair {
    Int(i64, i64),
    Float(f64, f64),
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

pub struct StateMachine {
    pub scenes: HashMap<SceneId, Scene>,
    pub op_results: OpResults,
    pub root_scene: Option<SceneId>,
    pub wakeup_proxy: Option<ImageEventLoopProxy>,
}

impl StateMachine {
    pub fn new_locked() -> Mutex<Self> {
        Mutex::new(Self {
            scenes: HashMap::new(),
            op_results: OpResults::new(),
            root_scene: None,
            wakeup_proxy: None,
        })
    }

    pub fn eval_ops_list(&self, ops: &[OpsOperation], scene_id: SceneId) -> Vec<Value> {
        let mut results = vec![];
        for op in ops.iter() {
            let val = self.eval_op(op, (scene_id, &results));
            results.push(val);
        }
        results
    }

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

    pub fn update_and_evaluate(&mut self, time: f64, width: i64, height: i64) {
        {
            let vars = &mut self
                .scenes
                .get_mut(&self.root_scene.unwrap())
                .unwrap()
                .1
                .var_vals;
            vars.insert(":time".to_string(), Value::Double(time));
            vars.insert(":width".to_string(), Value::Sint64(width));
            vars.insert(":height".to_string(), Value::Sint64(height));
        }

        let mut stack = vec![(self.root_scene.unwrap(), 0)];
        let mut watches_to_run = vec![];

        while !stack.is_empty() {
            let (scene_id, child_id) = stack.pop().unwrap();
            let (scene_desc, scene_state) = self.scenes.get(&scene_id).unwrap();

            if child_id == 0 {
                // Evaluate current scene
                eprintln!("[rnd:dbg] Evaluating scene #{scene_id}");
                let values = self.eval_ops_list(&scene_desc.ops, scene_id);
                eprintln!("[rnd:dbg]  -> {values:?}");
                self.op_results.vals.insert(scene_id, values);

                for (i, watch) in scene_desc.watches.iter().enumerate() {
                    let cond_val = self.op_results.get(watch.condition, (0, &[]));
                    match cond_val {
                        Value::Sint64(0) => continue,
                        Value::Sint64(_) => watches_to_run.push((scene_id, i)),
                        val => panic!("Watch condition must be of type Sint64, not: {:?}", val),
                    }
                }
            }
            if child_id < scene_state.children.len() {
                stack.push((scene_id, child_id + 1));
                let child = scene_state.children[child_id];
                stack.push((child, 0));
            } else {
                // no more children, bye
            }
        }

        for (scene_id, watch_id) in watches_to_run {
            eprintln!("[rnd:dbg] Running watch #{watch_id} of scene #{scene_id}");
            let watch = self
                .scenes
                .get(&scene_id)
                .unwrap()
                .0
                .watches
                .get(watch_id)
                .unwrap();
            let op_results = self.eval_ops_list(&watch.handler.ops, 0);
            let cmds = watch.handler.cmds.clone();
            for cmd in cmds.iter() {
                self.eval_handler_cmd(cmd, (0, &op_results));
            }
        }
    }

    pub fn get_default_window_size_for_scene(&mut self, scene: SceneId) -> Option<(i32, i32)> {
        let root_vars = &self.scenes.get(&scene).unwrap().1.var_vals;
        match (
            root_vars.get(":window_initial_size_x"),
            root_vars.get(":window_initial_size_y"),
        ) {
            (Some(w), Some(h)) => match (w, h) {
                (Value::Sint64(w), Value::Sint64(h)) => Some((*w as i32, *h as i32)),
                (_, _) => panic!(
                    "Initial window size must be of type Sint64, not: ({:?}, {:?})",
                    w, h
                ),
            },
            (_, _) => None,
        }
    }

    pub fn eval_handler_cmd(&mut self, cmd: &HandlerCmd, ctx: (SceneId, &[Value])) {
        match cmd {
            HandlerCmd::Nop => {}
            HandlerCmd::ReparentScene { scene, to } => {
                let root_scene = &mut self.root_scene;
                let scenes = &mut self.scenes;
                let parent = scenes.get(scene).unwrap().1.parent;

                // Disconnect from previous parent
                match parent {
                    SceneParent::NoParent | SceneParent::Hidden => {} // Already disconnected / hidden
                    SceneParent::Root => {
                        // Is Root
                        *root_scene = None;
                    }
                    SceneParent::Parent(prev_parent) => {
                        let parent = scenes.get_mut(&prev_parent).unwrap();
                        parent
                            .1
                            .children
                            .remove(parent.1.children.iter().position(|s| s == scene).unwrap());
                    }
                }
                self.scenes.get_mut(scene).unwrap().1.parent = SceneParent::NoParent;

                // Connect to new parent
                match to {
                    A2RReparentScene::Inside(inside_what) => {
                        self.scenes
                            .get_mut(inside_what)
                            .unwrap()
                            .1
                            .children
                            .insert(0, *scene);
                        self.scenes.get_mut(scene).unwrap().1.parent =
                            SceneParent::Parent(*inside_what);
                    }
                    A2RReparentScene::After(after_what) => {
                        let idx = self
                            .scenes
                            .get(&self.scenes.get(after_what).unwrap().1.parent.unwrap())
                            .unwrap()
                            .1
                            .children
                            .iter()
                            .position(|s| *s == *after_what)
                            .unwrap();
                        self.scenes
                            .get_mut(&self.scenes.get(after_what).unwrap().1.parent.unwrap())
                            .unwrap()
                            .1
                            .children
                            .insert(idx + 1, *scene);
                        self.scenes.get_mut(scene).unwrap().1.parent =
                            self.scenes.get(after_what).unwrap().1.parent;
                    }
                    A2RReparentScene::Root => {
                        if let Some(root_scene) = self.root_scene {
                            self.scenes.get_mut(&root_scene).unwrap().1.parent =
                                SceneParent::NoParent;
                        }
                        self.root_scene = Some(*scene);
                        self.scenes.get_mut(scene).unwrap().1.parent = SceneParent::Root;
                    }
                    A2RReparentScene::Disconnect => {} // Was already disconnected
                    A2RReparentScene::Hide => {
                        self.scenes.get_mut(scene).unwrap().1.parent = SceneParent::Hidden;
                    }
                }
            }
            HandlerCmd::UpdateVar { var, value } => {
                let var_value = self.op_results.get(*value, ctx).to_owned();
                let default_var_val = self
                    .scenes
                    .get_mut(&var.scene)
                    .unwrap()
                    .0
                    .var_decls
                    .get(&var.key)
                    .unwrap();

                // Typecheck
                match (&var_value, &default_var_val) {
                    (Value::Sint64(_), Value::Sint64(_)) => {},
                    (Value::Double(_), Value::Double(_)) => {},
                    (Value::String(_), Value::String(_)) => {},
                    (val, default) => panic!("Calculated value doesn't match declaration: Declared as {default:?}, Got: {val:?}"),
                }

                let var_vals = &mut self.scenes.get_mut(&var.scene).unwrap().1.var_vals;
                eprintln!(
                    "[rnd:dbg] Set {}.{} to {:?}",
                    var.scene, var.key, &var_value
                );
                var_vals.insert(var.key.to_owned(), var_value);
            }
            HandlerCmd::DebugMessage { msg: debug } => {
                eprintln!("[rnd:dbg] Reply: {}", debug);
            }
            HandlerCmd::If {
                condition,
                then,
                or_else,
            } => {
                let cond_value = self.op_results.get(*condition, ctx).to_owned();
                match cond_value {
                    Value::Sint64(0) => {
                        eprintln!("[rnd:dbg] Running else");
                        self.eval_handler_cmd(or_else, ctx);
                    }
                    Value::Sint64(_) => {
                        eprintln!("[rnd:dbg] Running then");
                        self.eval_handler_cmd(then, ctx);
                    }
                    _ => panic!(
                        "'If' conditions must be of type Sint64, not: {:?}",
                        cond_value
                    ),
                }
            }
        }
    }
}

pub struct Communicator<'a> {
    pub app_stdin: Box<dyn Write + Send>,
    pub app_stdout: Box<dyn Read + Send>,
    pub state_machine: &'a Mutex<StateMachine>,
    pub update_barrier: Option<Arc<Barrier>>,
}

impl<'a> Communicator<'a> {
    pub fn connect(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // Send hello
        {
            eprintln!("[rnd:dbg] sending hello");
            self.app_stdin.write_all(boldui_protocol::R2A_MAGIC)?;
            self.app_stdin
                .write_all(&bincode::serialize(&boldui_protocol::R2AHello {
                    min_protocol_major_version: boldui_protocol::LATEST_MAJOR_VER,
                    min_protocol_minor_version: boldui_protocol::LATEST_MINOR_VER,
                    max_protocol_major_version: boldui_protocol::LATEST_MAJOR_VER,
                    extra_len: 0, // No extra data
                })?)?;
            self.app_stdin.flush()?;
        }

        // Get hello response
        {
            eprintln!("[rnd:dbg] reading hello response");
            let mut magic = [0u8; boldui_protocol::A2R_MAGIC.len()];
            self.app_stdout.read_exact(&mut magic).unwrap();
            assert_eq!(&magic, boldui_protocol::A2R_MAGIC, "Missing magic");

            let hello_res = bincode::deserialize_from::<_, boldui_protocol::A2RHelloResponse>(
                &mut self.app_stdout,
            )?;

            assert_eq!(
                (
                    hello_res.protocol_major_version,
                    hello_res.protocol_minor_version
                ),
                (
                    boldui_protocol::LATEST_MAJOR_VER,
                    boldui_protocol::LATEST_MINOR_VER
                ),
                "[rnd:err] Incompatible version"
            );
            assert_eq!(
                hello_res.extra_len, 0,
                "[rnd:err] This protocol version specifies no extra data"
            );

            if let Some(err) = hello_res.error {
                panic!(
                    "[rnd:err] An error has occurred: code {}: {}",
                    err.code, err.text
                );
            }
            eprintln!("[rnd:dbg] connected!");
        }
        Ok(())
    }

    pub fn send_open(&mut self, path: String) -> Result<(), Box<dyn std::error::Error>> {
        eprintln!("[rnd:dbg] sending R2AOpen");
        self.app_stdin.send(&boldui_protocol::R2AMessage::Open(
            boldui_protocol::R2AOpen { path },
        ))?;

        Ok(())
    }

    pub fn main_loop(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut msg_buf = Vec::new();
        loop {
            let msg_len = self.app_stdout.read_u32::<LE>()?;
            eprintln!("[rnd:dbg] reading msg of size {}", msg_len);
            msg_buf.resize(msg_len as usize, 0);
            self.app_stdout.read_exact(&mut msg_buf)?;
            let msg = bincode::deserialize::<A2RMessage>(&msg_buf)?;

            eprintln!("[rnd:dbg] A2R: {:#?}", &msg);
            match msg {
                A2RMessage::Update(A2RUpdate {
                    updated_scenes,
                    run_blocks,
                }) => {
                    // Some frontends (e.g. image frontend) want to run between _each_ update, so wait for it to finish
                    if let Some(update_barrier) = &self.update_barrier {
                        update_barrier.wait();
                    }

                    // TODO: Create utilities for some of the repeated code here
                    let mut state = self.state_machine.lock();
                    for update in updated_scenes {
                        assert_ne!(update.id, 0, "The '0' scene ID is reserved");
                        let (scene_desc, scene_state) = state
                            .scenes
                            .entry(update.id)
                            .or_insert_with(|| (A2RUpdateScene::default(), SceneState::default()));
                        *scene_desc = update;

                        // Remove undeclared variables
                        let var_decl_keys = scene_desc
                            .var_decls
                            .iter()
                            .map(|(key, _)| key.as_str())
                            .collect::<HashSet<_>>();
                        scene_state
                            .var_vals
                            .retain(|key, _val| var_decl_keys.contains(key.as_str()));

                        // Populate with the default values
                        for (key, default_val) in scene_desc.var_decls.iter() {
                            scene_state
                                .var_vals
                                .entry(key.to_owned())
                                .or_insert_with(|| default_val.to_owned());
                        }
                    }

                    // Run handler blocks
                    for block in run_blocks.iter() {
                        let op_results = state.eval_ops_list(&block.ops, 0);
                        for cmd in block.cmds.iter() {
                            state.eval_handler_cmd(cmd, (0, &op_results));
                        }
                    }

                    // Remove scenes with no parent
                    state
                        .scenes
                        .retain(|_scene_id, scene| scene.1.parent.has_parent());

                    // Redraw
                    state.wakeup_proxy.as_ref().unwrap().request_redraw();

                    eprintln!("[rnd:dbg] New scenes: {:#?}", state.scenes);
                }
                A2RMessage::Error(e) => {
                    panic!("App Error: Code {}: {}", e.code, e.text);
                }
            }
        }
    }
}
