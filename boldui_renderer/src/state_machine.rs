use crate::communicator::{CommChannelRecv, CommChannelSend, FromStateMachine};
use crate::dmabuf::{ExternalApp, TextureStorageMetadata};
use crate::op_interpreter::{DepTracker, OpResults};
use crate::{EventLoopProxy, ToStateMachine};
use bimap_plus_map::BiMapPlusMap;
use boldui_protocol::{
    A2RReparentScene, A2RUpdateScene, EventType, ExternalAppRequest, HandlerBlock, HandlerCmd,
    OpsOperation, R2AReply, SceneId, Value, VarId,
};
use eventfd::{EfdFlags, EventFD};
use ordered_map::OrderedMap;
use skia_safe::gpu::BackendTexture;
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::os::fd::OwnedFd;
use std::time::Instant;
use tracing::{debug, trace, warn};

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
pub enum SceneReplacement {
    #[default]
    None,
    PendingExternalWidget {
        texture_metadata: TextureStorageMetadata,
        texture_fd: OwnedFd,
    },
    ExternalWidget {
        texture: BackendTexture,
    },
}

impl SceneReplacement {
    pub fn is_pending(&self) -> bool {
        matches!(self, SceneReplacement::PendingExternalWidget { .. })
    }

    /// Should only be called from a rendering context
    pub fn realise_pending_external_widget(&mut self) {
        let mut pending = SceneReplacement::None;
        std::mem::swap(self, &mut pending);
        if let SceneReplacement::PendingExternalWidget {
            texture_metadata,
            texture_fd,
        } = pending
        {
            let texture = ExternalApp::attach_remote_texture(&texture_metadata, texture_fd);
            *self = SceneReplacement::ExternalWidget { texture };
        } else {
            panic!("Called realise_pending_external_widget on a widget that's not pending")
        }
    }
}

#[derive(Debug, Default)]
pub struct SceneState {
    pub children: Vec<SceneId>,
    pub parent: SceneParent,
    pub var_vals: BTreeMap<String, Value>,
    pub scene_replacement: SceneReplacement,
}

pub type Scene = (A2RUpdateScene, SceneState);
pub type WindowId = u64;

#[derive(Default)]
pub struct WindowState {
    pub last_scene_size: (i32, i32),
    pub var_deps: BTreeSet<VarId>,
}

pub(crate) struct StateMachine {
    pub scenes: HashMap<SceneId, Scene>,
    pub op_results: OpResults,
    pub root_scenes: BiMapPlusMap<SceneId, WindowId, WindowState>,
    pub has_pending_replies: bool,
    pub comm_channel_send: CommChannelSend,
    pub event_proxy: Option<Box<dyn EventLoopProxy + Send>>,
    pub timebase: Instant,
    pub wakeups: OrderedMap<SceneId, f64, f64>,
}

impl StateMachine {
    pub fn new() -> (Self, CommChannelRecv) {
        let (comm_channel_send, comm_channel_recv) = crossbeam::channel::unbounded();
        let notifier = EventFD::new(0, EfdFlags::empty()).unwrap();
        (
            Self {
                scenes: HashMap::new(),
                op_results: OpResults::new(),
                root_scenes: BiMapPlusMap::new(),
                has_pending_replies: false,
                comm_channel_send: CommChannelSend {
                    send: comm_channel_send,
                    notify_send: notifier.clone(),
                },
                event_proxy: None,
                timebase: Instant::now(),
                wakeups: OrderedMap::new(|v| -*v), // Negate for ascending order
            },
            CommChannelRecv {
                recv: comm_channel_recv,
                notify_recv: notifier,
            },
        )
    }

    pub fn eval_ops_list(
        &self,
        ops: &[OpsOperation],
        scene_id: SceneId,
        dep_tracker: &mut DepTracker,
    ) -> Vec<Value> {
        let mut results = vec![];
        for op in ops.iter() {
            let val = self.eval_op(op, (scene_id, &results), dep_tracker);
            results.push(val);
        }
        results
    }

    pub fn update_and_evaluate(&mut self, scene_id: SceneId, scene_width: i64, scene_height: i64) {
        if self.root_scenes.bimap_get_by_left(&scene_id).is_none() {
            warn!(scene_id, "Tried to update scene which is not a root scene");
            return;
        }
        // TODO: Create utilities for some of the repeated code here
        {
            let vars = &mut self.scenes.get_mut(&scene_id).unwrap().1.var_vals;
            vars.insert(":width".to_string(), Value::Sint64(scene_width));
            vars.insert(":height".to_string(), Value::Sint64(scene_height));
        }

        let mut stack = vec![(scene_id, 0)];
        let mut watches_to_run = vec![];
        let mut dep_tracker = self.get_dep_tracker();

        while !stack.is_empty() {
            let (scene_id, child_id) = stack.pop().unwrap();
            let (scene_desc, scene_state) = self.scenes.get(&scene_id).unwrap();

            if child_id == 0 {
                // Evaluate current scene
                trace!(scene_id, "Evaluating scene");
                let values = self.eval_ops_list(&scene_desc.ops, scene_id, &mut dep_tracker);
                trace!(scene_id, "  -> {values:?}");
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

        // Update next wakeup, according to info collected during last update
        self.wakeups.insert(scene_id, dep_tracker.next_wakeup());

        // Run watches
        for (scene_id, watch_id) in watches_to_run {
            trace!(scene_id, watch_id, "Running watch");
            let watch = self
                .scenes
                .get(&scene_id)
                .unwrap()
                .0
                .watches
                .get(watch_id)
                .unwrap();
            let op_results = self.eval_ops_list(&watch.handler.ops, 0, &mut dep_tracker);
            let cmds = watch.handler.cmds.clone();
            for cmd in cmds.iter() {
                self.eval_handler_cmd(cmd, (0, &op_results), &mut dep_tracker);
            }
        }

        let (var_deps, _updated_vars) = dep_tracker.into_var_info();
        trace!(scene_id, "var deps of scene -> {:?}", var_deps);
        self.root_scenes
            .hashmap_get_mut_by_left(&scene_id)
            .unwrap()
            .var_deps = var_deps;

        if self.has_pending_replies {
            // Sending a character on this pipe signifies the `reply_recv` end of the channel is ready for reading
            self.comm_channel_send.notify_send.write(1).unwrap();
            self.has_pending_replies = false;
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

    pub fn get_window_title_for_scene(&mut self, scene: SceneId) -> Option<String> {
        let root_vars = &self.scenes.get(&scene).unwrap().1.var_vals;
        match root_vars.get(":window_title") {
            Some(title) => match title {
                Value::String(s) => Some(s.clone()),
                _ => panic!("Window title must be of type String, not: {:?}", title),
            },
            _ => None,
        }
    }

    pub fn eval_handler_cmd(
        &mut self,
        cmd: &HandlerCmd,
        ctx: (SceneId, &[Value]),
        dep_tracker: &mut DepTracker,
    ) {
        match cmd {
            HandlerCmd::Nop => {}
            HandlerCmd::ReparentScene { scene, to } => {
                let scenes = &mut self.scenes;
                let parent = scenes.get(scene).unwrap().1.parent;

                // Disconnect from previous parent
                match parent {
                    SceneParent::NoParent | SceneParent::Hidden => {} // Already disconnected / hidden
                    SceneParent::Root => {
                        // Is Root
                        self.root_scenes.remove_by_left(scene);
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
                        self.scenes.get_mut(scene).unwrap().1.parent = SceneParent::Root;
                        self.event_proxy
                            .as_ref()
                            .unwrap()
                            .to_state_machine(ToStateMachine::AllocWindow(*scene));
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
                    (Value::Color(_), Value::Color(_)) => {},
                    (Value::Point { .. }, Value::Point { .. }) => {},
                    (Value::Rect { .. }, Value::Rect { .. }) => {},
                    (val, default) => panic!("Calculated value doesn't match declaration: Declared as {default:?}, Got: {val:?}"),
                }

                let var_vals = &mut self.scenes.get_mut(&var.scene).unwrap().1.var_vals;
                trace!("Set {}@{} to {:?}", var.key, var.scene, &var_value);
                dep_tracker.add_updated_var(var.scene, var.key.to_owned());
                var_vals.insert(var.key.to_owned(), var_value);
            }
            HandlerCmd::DebugMessage { msg } => {
                debug!("DebugMessage: {}", msg);
            }
            HandlerCmd::Reply { path, params } => {
                let reply = R2AReply {
                    path: path.to_owned(),
                    params: params
                        .iter()
                        .map(|opid| self.op_results.get(*opid, ctx).to_owned())
                        .collect(),
                };
                trace!("Replying: {:?}", reply);
                self.comm_channel_send
                    .send
                    .send(FromStateMachine::Reply(reply))
                    .unwrap();
                self.has_pending_replies = true;
            }
            HandlerCmd::If {
                condition,
                then,
                or_else,
            } => {
                let cond_value = self.op_results.get(*condition, ctx).to_owned();
                match cond_value {
                    Value::Sint64(0) => {
                        trace!("Running else");
                        self.eval_handler_cmd(or_else, ctx, dep_tracker);
                    }
                    Value::Sint64(_) => {
                        trace!("Running then");
                        self.eval_handler_cmd(then, ctx, dep_tracker);
                    }
                    _ => panic!(
                        "'If' conditions must be of type Sint64, not: {:?}",
                        cond_value
                    ),
                }
            }
            HandlerCmd::AllocateWindowId => unimplemented!(),
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
                .keys()
                .map(|key| key.as_str())
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
        let mut dep_tracker = self.get_dep_tracker();
        for block in run_blocks.iter() {
            let op_results = self.eval_ops_list(&block.ops, 0, &mut dep_tracker);
            for cmd in block.cmds.iter() {
                self.eval_handler_cmd(cmd, (0, &op_results), &mut dep_tracker);
            }
        }

        if self.has_pending_replies {
            // Sending a character on this pipe signifies the `reply_recv` end of the channel is ready for reading
            self.comm_channel_send.notify_send.write(1).unwrap();
            self.has_pending_replies = false;
        }

        // Remove scenes with no parent
        self.scenes
            .retain(|_scene_id, scene| scene.1.parent.has_parent());

        // Redraw scenes affected by changes
        trace!("updated vars -> {:?}", dep_tracker.get_updated_vars());
        self.queue_redraw_affected_scenes(dep_tracker.get_updated_vars());

        trace!("New scenes: {:#?}", self.scenes);
    }

    pub(crate) fn handle_ext_app_requests(&mut self, requests: Vec<ExternalAppRequest>) {
        for request in requests {
            trace!("Sending external app request: {:?}", request);
            self.comm_channel_send
                .send
                .send(FromStateMachine::RequestExternalWidget {
                    scene_id: request.scene_id,
                    uri: request.uri,
                })
                .unwrap();
            self.comm_channel_send.notify_send.write(1).unwrap();
        }
    }

    // Only supports root scenes
    pub(crate) fn handle_click(
        &mut self,
        scene_id: SceneId,
        scene_width: i64,
        scene_height: i64,
        x: f64,
        y: f64,
        button: u8,
    ) {
        // TODO: Create utilities for some of the repeated code here
        {
            let vars = &mut self.scenes.get_mut(&scene_id).unwrap().1.var_vals;
            vars.insert(":width".to_string(), Value::Sint64(scene_width));
            vars.insert(":height".to_string(), Value::Sint64(scene_height));
            vars.insert(":click_x".to_string(), Value::Double(x));
            vars.insert(":click_y".to_string(), Value::Double(y));
            vars.insert(":click_btn".to_string(), Value::Sint64(button as i64));
        }

        let mut stack = vec![(scene_id, 0)];
        let mut event_handlers_to_run = vec![];
        let mut dep_tracker = self.get_dep_tracker();

        while !stack.is_empty() {
            let (scene_id, child_id) = stack.pop().unwrap();
            let (scene_desc, scene_state) = self.scenes.get(&scene_id).unwrap();

            if child_id == 0 {
                // Evaluate current scene
                trace!(scene_id, "Evaluating scene for inputs");
                let values = self.eval_ops_list(&scene_desc.ops, scene_id, &mut dep_tracker);
                trace!(scene_id, "  -> {values:?}");
                self.op_results.vals.insert(scene_id, values);

                for (i, (evt_type, _handler)) in scene_desc.event_handlers.iter().enumerate() {
                    match evt_type {
                        EventType::Click { rect } => {
                            let rect = self.op_results.get(*rect, (0, &[]));
                            let (left, top, right, bottom) = match rect {
                                Value::Rect {
                                    left,
                                    top,
                                    right,
                                    bottom,
                                } => (left, top, right, bottom),
                                _ => panic!("Invalid type for 'rect' param of 'DrawRect' cmd"),
                            };
                            if x >= *left && x <= *right && y >= *top && y <= *bottom {
                                event_handlers_to_run.push((scene_id, i))
                            }
                        }
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

        for (scene_id, evt_hnd_id) in event_handlers_to_run {
            trace!(scene_id, evt_hnd_id, "Running event handler");
            let (_event_type, handler) = self
                .scenes
                .get(&scene_id)
                .unwrap()
                .0
                .event_handlers
                .get(evt_hnd_id)
                .unwrap();
            let op_results = self.eval_ops_list(&handler.ops, 0, &mut dep_tracker);
            let cmds = handler.cmds.clone();
            for cmd in cmds.iter() {
                self.eval_handler_cmd(cmd, (0, &op_results), &mut dep_tracker);
            }
        }

        trace!(
            scene_id,
            "click: updated vars -> {:?}",
            dep_tracker.get_updated_vars()
        );
        self.queue_redraw_affected_scenes(dep_tracker.get_updated_vars());

        if self.has_pending_replies {
            // Sending a character on this pipe signifies the `reply_recv` end of the channel is ready for reading
            self.comm_channel_send.notify_send.write(1).unwrap();
            self.has_pending_replies = false;
        }
    }

    pub fn register_window_for_scene(&mut self, scene_id: SceneId, window_id: WindowId) {
        self.root_scenes
            .insert(scene_id, window_id, WindowState::default());
        self.wakeups.insert(scene_id, f64::INFINITY);
    }

    fn queue_redraw_affected_scenes(&mut self, updated_vars: &BTreeSet<VarId>) {
        let mut scenes_to_update: BTreeSet<SceneId> = BTreeSet::new();
        for (scene, window_state) in self.root_scenes.left_items_iter() {
            for updated_var in updated_vars.iter() {
                if window_state.var_deps.contains(updated_var) {
                    scenes_to_update.insert(*scene);
                }
            }
        }
        for scene in scenes_to_update.into_iter() {
            self.event_proxy
                .as_ref()
                .unwrap()
                .to_state_machine(ToStateMachine::Redraw {
                    window_id: *self.root_scenes.bimap_get_by_left(&scene).unwrap(),
                });
        }
    }

    fn get_dep_tracker(&self) -> DepTracker {
        DepTracker::new(self.timebase.elapsed().as_secs_f64())
    }
}
