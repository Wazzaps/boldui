use crate::renderer::Renderer;
use crate::simulator::Simulator;
use crate::state_machine::WindowId;
use crate::{EventLoopProxy, Frontend, StateMachine, ToStateMachine};
use boldui_protocol::A2RUpdate;
use crossbeam::channel::{Receiver, RecvTimeoutError, Sender};
use skia_safe::{AlphaType, Color4f, ColorSpace, EncodedImageFormat, ISize, ImageInfo, Surface};
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::time::Instant;
use tracing::{debug, error, info, trace};

#[derive(Default)]
pub(crate) struct InternalWindowState {
    pub frame_num: u64,
}

pub(crate) struct ImageFrontend {
    pub event_recv: Receiver<ToStateMachine>,
    pub renderer: Renderer,
    pub state_machine: StateMachine,
    pub simulator: Option<Simulator>,
    pub window_counter: u64,
    pub windows: HashMap<u64, InternalWindowState>,
}

#[derive(Clone)]
pub(crate) struct ImageEventLoopProxy {
    pub event_send: Sender<ToStateMachine>,
}

impl EventLoopProxy for ImageEventLoopProxy {
    fn to_state_machine(&self, event: ToStateMachine) {
        self.event_send.send(event).unwrap();
    }
}

impl ImageFrontend {
    pub fn new(
        renderer: Renderer,
        mut state_machine: StateMachine,
        simulator: Option<Simulator>,
    ) -> (ImageFrontend, Box<ImageEventLoopProxy>) {
        let (event_send, event_recv) = crossbeam::channel::unbounded();
        let event_proxy = Box::new(ImageEventLoopProxy { event_send });
        state_machine.event_proxy = Some(event_proxy.clone());
        (
            Self {
                event_recv,
                renderer,
                state_machine,
                simulator,
                window_counter: 0,
                windows: HashMap::new(),
            },
            event_proxy,
        )
    }
}

impl Frontend for ImageFrontend {
    fn main_loop(&mut self) {
        let mut next_wakeup: Option<Instant> = None;
        loop {
            let event = match next_wakeup {
                // No wakeup scheduled, there must be an event coming next
                None => self.event_recv.recv().unwrap_or(ToStateMachine::Quit),

                // Wakeup scheduled
                Some(next_wakeup_instant) => {
                    match self.event_recv.recv_deadline(next_wakeup_instant) {
                        // Got an event before the wakeup
                        Ok(e) => e,

                        // Woke up before any event
                        Err(RecvTimeoutError::Timeout) => {
                            next_wakeup = None;
                            // FIXME: Always redraws first window
                            ToStateMachine::Redraw { window_id: 0 }
                        }

                        // Bye
                        Err(RecvTimeoutError::Disconnected) => ToStateMachine::Quit,
                    }
                }
            };

            let start = Instant::now();
            match event {
                ToStateMachine::Update(A2RUpdate {
                    updated_scenes,
                    run_blocks,
                    external_app_requests,
                }) => {
                    self.state_machine
                        .update_scenes_and_run_blocks(updated_scenes, run_blocks);
                    self.state_machine
                        .handle_ext_app_requests(external_app_requests);
                    trace!("A2R update took {:?} to handle", start.elapsed());
                    self.state_machine
                        .event_proxy
                        .as_ref()
                        .unwrap()
                        .to_state_machine(ToStateMachine::SimulatorTick { from_update: true });
                }
                ToStateMachine::Redraw { window_id } => {
                    self.redraw(start, window_id);
                    self.state_machine
                        .event_proxy
                        .as_ref()
                        .unwrap()
                        .to_state_machine(ToStateMachine::SimulatorTick { from_update: false });
                }
                ToStateMachine::SimulatorTick { from_update } => {
                    if let Some(simulator) = &mut self.simulator {
                        if let Err(e) = simulator.tick(&mut self.state_machine, from_update) {
                            error!("Error while running simulator: {e:?}");
                            break;
                        }
                    }
                }
                ToStateMachine::Quit => {
                    info!("State machine seems to be done, bye from frontend!");
                    break;
                }
                ToStateMachine::SleepUntil(instant) => {
                    // Select the earliest wakeup time
                    next_wakeup =
                        next_wakeup.map_or(Some(instant), |before| Some(before.min(instant)));
                }
                ToStateMachine::Click {
                    window_id,
                    x,
                    y,
                    button,
                } => {
                    let scene_id = *self
                        .state_machine
                        .root_scenes
                        .bimap_get_by_right(&window_id)
                        .unwrap();
                    let last_scene_size = self
                        .state_machine
                        .root_scenes
                        .hashmap_get_by_right(&window_id)
                        .unwrap()
                        .last_scene_size;

                    trace!(
                        scene_id,
                        window_id,
                        "[{:?}] Updated for click",
                        start.elapsed()
                    );

                    self.state_machine.handle_click(
                        scene_id,
                        last_scene_size.0 as i64,
                        last_scene_size.1 as i64,
                        x,
                        y,
                        button,
                    );
                    trace!(scene_id, window_id, "[{:?}] Handled click", start.elapsed());
                }
                ToStateMachine::AllocWindow(scene_id) => {
                    trace!(scene_id, "Allocating window");
                    self.windows
                        .insert(self.window_counter, InternalWindowState::default());
                    self.state_machine
                        .register_window_for_scene(scene_id, self.window_counter);
                    self.window_counter += 1;
                }
                ToStateMachine::MountExternalWidget {
                    scene_id,
                    texture_metadata,
                    texture_fd,
                } => {
                    info!(scene_id, "Mounting external widget");
                }
            }
        }
    }
}

impl ImageFrontend {
    fn redraw(&mut self, start: Instant, window_id: WindowId) {
        let scene_id = *self
            .state_machine
            .root_scenes
            .bimap_get_by_right(&window_id)
            .unwrap();

        let window_size = {
            const DEFAULT_WINDOW_SIZE: (i32, i32) = (1280, 720);
            self.state_machine
                .get_default_window_size_for_scene(scene_id)
                .unwrap_or(DEFAULT_WINDOW_SIZE)
        };

        let window_state = self
            .state_machine
            .root_scenes
            .hashmap_get_mut_by_right(&window_id)
            .unwrap();
        window_state.last_scene_size = window_size;

        // Create canvas
        let color_space = ColorSpace::new_srgb();
        let img_size = ISize::new(window_size.0, window_size.1);
        let image_info = ImageInfo::new_n32(img_size, AlphaType::Unpremul, color_space);
        let mut surface = Surface::new_raster(&image_info, image_info.min_row_bytes(), None)
            .expect("Failed to create surface");
        let canvas = surface.canvas();
        debug!(
            scene_id,
            window_id,
            "[{:?}] Created canvas",
            start.elapsed()
        );

        // Render
        canvas.clear(Color4f::new(0.0, 0.0, 0.0, 0.0));
        {
            self.state_machine.update_and_evaluate(
                scene_id,
                img_size.width as i64,
                img_size.height as i64,
            );
            trace!(scene_id, window_id, "[{:?}] Updated", start.elapsed());
            self.renderer
                .render_scene(canvas, &mut self.state_machine, scene_id);
            trace!(scene_id, window_id, "[{:?}] Rendered", start.elapsed());
        }
        trace!(
            scene_id,
            window_id,
            window_id,
            "Frame took {:?} to render",
            start.elapsed()
        );

        // Encode it
        let frame_num_ref = &mut self.windows.get_mut(&window_id).unwrap().frame_num;
        let frame_num = *frame_num_ref;
        let mut out = BufWriter::new(
            File::create(format!("target/result-wnd{window_id}-frm{frame_num}.png")).unwrap(),
        );
        let img = surface
            .image_snapshot()
            .encode_to_data(EncodedImageFormat::PNG)
            .expect("Failed to encode as PNG");
        out.write_all(img.as_bytes()).expect("Failed to write PNG");
        info!(scene_id, window_id, "Wrote frame #{frame_num}");
        *frame_num_ref += 1;
    }
}
