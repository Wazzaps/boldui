use crate::renderer::Renderer;
use crate::simulator::Simulator;
use crate::{EventLoopProxy, Frontend, StateMachine, ToStateMachine};
use boldui_protocol::A2RUpdate;
use crossbeam::channel::{Receiver, RecvTimeoutError, Sender};
use skia_safe::{AlphaType, Color4f, ColorSpace, EncodedImageFormat, ISize, ImageInfo, Surface};
use std::fs::File;
use std::io::{BufWriter, Write};
use std::time::Instant;

pub(crate) struct ImageFrontend {
    pub event_recv: Receiver<ToStateMachine>,
    pub renderer: Renderer,
    pub state_machine: StateMachine,
    pub simulator: Option<Simulator>,
    pub frame_num: u64,
    pub last_scene_size: (i32, i32),
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
                frame_num: 0,
                last_scene_size: (0, 0),
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
                            ToStateMachine::Redraw
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
                }) => {
                    self.state_machine
                        .update_scenes_and_run_blocks(updated_scenes, run_blocks);
                    eprintln!("[rnd:dbg] A2R update took {:?} to handle", start.elapsed());
                    self.state_machine
                        .event_proxy
                        .as_ref()
                        .unwrap()
                        .to_state_machine(ToStateMachine::SimulatorTick { from_update: true });
                }
                ToStateMachine::Redraw => {
                    self.redraw(start);
                    self.state_machine
                        .event_proxy
                        .as_ref()
                        .unwrap()
                        .to_state_machine(ToStateMachine::SimulatorTick { from_update: false });
                }
                ToStateMachine::SimulatorTick { from_update } => {
                    if let Some(simulator) = &mut self.simulator {
                        if let Err(e) = simulator.tick(&mut self.state_machine, from_update) {
                            eprintln!("[rnd:err] Error while running simulator: {:?}", e);
                            break;
                        }
                    }
                }
                ToStateMachine::Quit => {
                    eprintln!("[rnd:ntc] State machine seems to be done, bye from frontend!");
                    break;
                }
                ToStateMachine::SleepUntil(instant) => {
                    // Select the earliest wakeup time
                    next_wakeup =
                        next_wakeup.map_or(Some(instant), |before| Some(before.min(instant)));
                }
                ToStateMachine::Click { x, y, button } => {
                    self.state_machine.update_and_evaluate(
                        0.0,
                        self.last_scene_size.0 as i64,
                        self.last_scene_size.1 as i64,
                    );
                    eprintln!("[rnd:dbg] [{:?}] Updated for click", start.elapsed());
                    // TODO: Handle clicks per-scene
                    if let Some(_root_scene) = self.state_machine.root_scene {
                        self.state_machine.handle_click(
                            // root_scene,
                            0.0,
                            self.last_scene_size.0 as i64,
                            self.last_scene_size.1 as i64,
                            x,
                            y,
                            button,
                        );
                    }
                    eprintln!("[rnd:dbg] [{:?}] Handled click", start.elapsed());
                }
            }
        }
    }
}

impl ImageFrontend {
    fn redraw(&mut self, start: Instant) {
        // Get window size
        let window_size = {
            const DEFAULT_WINDOW_SIZE: (i32, i32) = (1280, 720);
            let root_scene = self.state_machine.root_scene.unwrap();
            self.state_machine
                .get_default_window_size_for_scene(root_scene)
                .unwrap_or(DEFAULT_WINDOW_SIZE)
        };
        self.last_scene_size = window_size;

        // Create canvas
        let color_space = ColorSpace::new_srgb();
        let img_size = ISize::new(window_size.0, window_size.1);
        let image_info = ImageInfo::new_n32(img_size, AlphaType::Unpremul, color_space);
        let mut surface = Surface::new_raster(&image_info, image_info.min_row_bytes(), None)
            .expect("Failed to create surface");
        let canvas = surface.canvas();
        eprintln!("[rnd:dbg] [{:?}] Created canvas", start.elapsed());

        // Render
        canvas.clear(Color4f::new(0.0, 0.0, 0.0, 0.0));
        {
            self.state_machine.update_and_evaluate(
                0.0,
                img_size.width as i64,
                img_size.height as i64,
            );
            eprintln!("[rnd:dbg] [{:?}] Updated", start.elapsed());
            match self.state_machine.root_scene {
                None => {
                    canvas.clear(Color4f::new(0.5, 0.1, 0.1, 1.0));
                }
                Some(root_scene) => {
                    self.renderer
                        .render_scene(canvas, &mut self.state_machine, root_scene);
                }
            }
            eprintln!("[rnd:dbg] [{:?}] Rendered", start.elapsed());
        }
        eprintln!("[rnd:dbg] Frame took {:?} to render", start.elapsed());

        // Encode it
        let frame_num = self.frame_num;
        let mut out =
            BufWriter::new(File::create(format!("target/result-{frame_num}.png")).unwrap());
        let img = surface
            .image_snapshot()
            .encode_to_data(EncodedImageFormat::PNG)
            .expect("Failed to encode as PNG");
        out.write_all(img.as_bytes()).expect("Failed to write PNG");
        eprintln!("[rnd:dbg] Wrote frame #{frame_num}");
        self.frame_num += 1;
    }
}
