use crate::op_interpreter::OpResults;
use crate::EventLoopProxy;
use boldui_protocol::{
    A2RReparentScene, A2RUpdateScene, HandlerBlock, HandlerCmd, OpsOperation, SceneId, Value,
};
use parking_lot::Mutex;
use std::collections::{BTreeMap, HashMap, HashSet};

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

pub(crate) struct StateMachine {
    pub scenes: HashMap<SceneId, Scene>,
    pub op_results: OpResults,
    pub root_scene: Option<SceneId>,
    pub wakeup_proxy: Option<Box<dyn EventLoopProxy + Send>>,
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

    pub fn update_scenes_and_run_blocks(
        &mut self,
        updated_scenes: Vec<A2RUpdateScene>,
        run_blocks: Vec<HandlerBlock>,
    ) {
        // Handle updated scenes
        for update in updated_scenes {
            assert_ne!(update.id, 0, "The '0' scene ID is reserved");
            let (scene_desc, scene_state) = self
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
            let op_results = self.eval_ops_list(&block.ops, 0);
            for cmd in block.cmds.iter() {
                self.eval_handler_cmd(cmd, (0, &op_results));
            }
        }

        // Remove scenes with no parent
        self.scenes
            .retain(|_scene_id, scene| scene.1.parent.has_parent());

        // Redraw
        self.wakeup_proxy.as_ref().unwrap().request_redraw();

        eprintln!("[rnd:dbg] New scenes: {:#?}", self.scenes);
    }
}
