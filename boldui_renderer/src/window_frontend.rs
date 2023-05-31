use crate::renderer::Renderer;
use crate::simulator::Simulator;
use crate::state_machine::{SceneReplacement, WindowId};
use crate::{Frontend, StateMachine, ToStateMachine};
use adw::prelude::{ApplicationExt, ApplicationExtManual};
use adw::{Application, HeaderBar};
use boldui_protocol::{A2RUpdate, SceneId};
use glib::{Continue, MainContext, SourceId, PRIORITY_DEFAULT};
use gtk::prelude::{BoxExt, GLAreaExt, GtkWindowExt, WidgetExt};
use gtk::{gio, GLArea};
use skia_safe::gpu::gl::FramebufferInfo;
use skia_safe::gpu::{BackendRenderTarget, RecordingContext, SurfaceOrigin};
use skia_safe::{Color4f, ColorType, Surface};
use std::cell::RefCell;
use std::collections::HashMap;
use std::ptr;
use std::rc::Rc;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};
use tracing::{debug, error, info, trace};

pub(crate) struct WindowFrontend {
    pub event_recv: Option<glib::Receiver<ToStateMachine>>,
    pub renderer: Option<Renderer>,
    pub state_machine: Option<StateMachine>,
    pub simulator: Option<Simulator>,
}

impl crate::EventLoopProxy for glib::Sender<ToStateMachine> {
    fn to_state_machine(&self, event: ToStateMachine) {
        self.send(event).unwrap();
    }
}

impl WindowFrontend {
    pub fn new(
        renderer: Renderer,
        mut state_machine: StateMachine,
        simulator: Option<Simulator>,
    ) -> (Self, Box<glib::Sender<ToStateMachine>>) {
        let (sender, receiver) = MainContext::channel(PRIORITY_DEFAULT);
        let event_proxy = Box::new(sender);
        state_machine.event_proxy = Some(event_proxy.clone());
        (
            Self {
                event_recv: Some(receiver),
                renderer: Some(renderer),
                state_machine: Some(state_machine),
                simulator,
            },
            event_proxy,
        )
    }
}

struct WindowState {
    win: adw::Window,
    gl_area: GLArea,
}

impl WindowState {
    pub(crate) fn new(
        app: &Application,
        renderer: Rc<RefCell<Renderer>>,
        state_machine: Rc<RefCell<StateMachine>>,
        wakeup_manager: Rc<RefCell<WakeupManager>>,
        window_id: WindowId,
        scene_id: SceneId,
    ) -> Self {
        let content = gtk::Box::new(gtk::Orientation::Vertical, 0);
        let gl_area = GLArea::builder().hexpand(true).vexpand(true).build();
        gl_area.connect_realize(|_widget| {
            // Load GL pointers from epoxy (GL context management library used by GTK).
            #[cfg(target_os = "macos")]
            let library =
                unsafe { libloading::os::unix::Library::new("libepoxy.0.dylib") }.unwrap();
            #[cfg(all(unix, not(target_os = "macos")))]
            let library = unsafe { libloading::os::unix::Library::new("libepoxy.so.0") }.unwrap();
            #[cfg(windows)]
            let library =
                libloading::os::windows::Library::open_already_loaded("epoxy-0.dll").unwrap();
            epoxy::load_with(|name| {
                unsafe { library.get::<_>(name.as_bytes()) }
                    .map(|symbol| *symbol)
                    .unwrap_or(ptr::null())
            });
            gl::load_with(epoxy::get_proc_addr);
        });
        let total_frametime_us = Box::leak(Box::new(AtomicU64::new(0)));
        let total_frames = Box::leak(Box::new(AtomicU64::new(0)));
        let min_frametime_us = Box::leak(Box::new(AtomicU64::new(999999999)));
        let max_frametime_us = Box::leak(Box::new(AtomicU64::new(0)));
        let state_machine2 = state_machine.clone();
        gl_area.connect_render(move |widget, _gl_ctx| {
            use gl::types::*;

            trace!(scene_id, "rendering scene");
            let start = Instant::now();
            let fb_info = {
                let mut fboid: GLint = 0;
                unsafe { gl::GetIntegerv(gl::FRAMEBUFFER_BINDING, &mut fboid) };

                FramebufferInfo {
                    fboid: fboid.try_into().unwrap(),
                    format: skia_safe::gpu::gl::Format::RGBA8.into(),
                }
            };
            let backend_render_target = BackendRenderTarget::new_gl(
                (widget.width(), widget.height()),
                // FIXME: correct multisampling and stencil bits
                0, // pixel_format.multisampling.map(|s| s.try_into().unwrap()),
                0, // pixel_format.stencil_bits.try_into().unwrap(),
                fb_info,
            );
            let gr_context = skia_safe::gpu::DirectContext::new_gl(None, None).unwrap();
            let mut rec_context = RecordingContext::from(gr_context);
            let mut surface = Surface::from_backend_render_target(
                &mut rec_context,
                &backend_render_target,
                SurfaceOrigin::BottomLeft,
                ColorType::RGBA8888,
                None,
                None,
            )
            .unwrap();
            let canvas = surface.canvas();
            let mut state_machine = (*state_machine2).borrow_mut();

            // Update last scene size
            {
                let window_state = state_machine
                    .root_scenes
                    .hashmap_get_mut_by_left(&scene_id)
                    .unwrap();
                window_state.last_scene_size = (widget.width(), widget.height());
            }

            // TODO: Decouple updates and re-renders, because watches might need to be triggered without re-rendering
            state_machine.update_and_evaluate(
                scene_id,
                widget.width() as i64,
                widget.height() as i64,
            );
            canvas.clear(Color4f::new(0.2, 0.2, 0.2, 1.0));
            (*renderer)
                .borrow_mut()
                .render_scene(canvas, &mut state_machine, scene_id);
            surface.flush();

            let elapsed_us = start.elapsed().as_micros() as u64;
            total_frametime_us.fetch_add(elapsed_us, Ordering::SeqCst);
            let frame_num = total_frames.fetch_add(1, Ordering::SeqCst);
            min_frametime_us.fetch_min(elapsed_us, Ordering::SeqCst);
            max_frametime_us.fetch_max(elapsed_us, Ordering::SeqCst);
            if frame_num % 100 == 0 {
                debug!(
                    scene_id,
                    "Render Timings: Min: {}us\tAvg: {}us\tMax: {}us",
                    min_frametime_us.load(Ordering::SeqCst),
                    total_frametime_us.load(Ordering::SeqCst) / total_frames.load(Ordering::SeqCst),
                    max_frametime_us.load(Ordering::SeqCst)
                );
            }

            state_machine
                .event_proxy
                .as_ref()
                .unwrap()
                .to_state_machine(ToStateMachine::SimulatorTick { from_update: false });

            drop(state_machine);
            wakeup_manager.update_next_wakeup();

            glib::signal::Inhibit(false)
        });

        let event_controller = gtk::GestureClick::new();

        event_controller.connect_released(move |_controller, button, x, y| {
            let mut state_machine = (*state_machine).borrow_mut();
            state_machine
                .event_proxy
                .as_mut()
                .unwrap()
                .to_state_machine(ToStateMachine::Click {
                    window_id,
                    x,
                    y,
                    button: button
                        .try_into()
                        .unwrap_or_else(|_| panic!("unexpected button id {button}")),
                });
        });

        gl_area.add_controller(event_controller);

        // Adwaitas' Window does not include a HeaderBar
        let header_bar = HeaderBar::new();
        content.append(&header_bar);
        content.append(&gl_area);
        let win = adw::Window::builder()
            .application(app)
            .title("Window")
            .default_width(300)
            .default_height(300)
            .content(&content)
            .build();

        Self { win, gl_area }
    }
}

impl Frontend for WindowFrontend {
    fn main_loop(&mut self) {
        let state_machine = Rc::new(RefCell::new(self.state_machine.take().unwrap()));
        let wakeup_manager = WakeupManager::new(state_machine.clone());
        let renderer = Rc::new(RefCell::new(self.renderer.take().unwrap()));
        let mut simulator = self.simulator.take();
        let event_recv = self.event_recv.take().unwrap();
        let windows: RefCell<HashMap<u64, WindowState>> = RefCell::new(HashMap::new());
        let window_counter = AtomicU64::new(10);

        let application = Application::builder()
            .application_id("org.boldos.ui.BoldUI")
            .build();

        let app = application.clone();
        event_recv.attach(None, move |event| {
            match event {
                ToStateMachine::Update(A2RUpdate {
                    updated_scenes,
                    run_blocks,
                    external_app_requests,
                }) => {
                    let start = Instant::now();
                    let mut state_machine = (*state_machine).borrow_mut();
                    state_machine.update_scenes_and_run_blocks(updated_scenes, run_blocks);
                    state_machine.handle_ext_app_requests(external_app_requests);
                    trace!("A2R update took {:?} to handle", start.elapsed());
                    state_machine
                        .event_proxy
                        .as_ref()
                        .unwrap()
                        .to_state_machine(ToStateMachine::SimulatorTick { from_update: true });
                }
                ToStateMachine::Redraw { window_id } => {
                    windows
                        .borrow_mut()
                        .get(&window_id)
                        .unwrap()
                        .gl_area
                        .queue_draw();
                }
                ToStateMachine::SimulatorTick { from_update } => {
                    if let Some(simulator) = &mut simulator {
                        if let Err(e) =
                            simulator.tick(&mut (*state_machine).borrow_mut(), from_update)
                        {
                            error!("Error while running simulator: {e:?}");
                            app.quit();
                            // *control_flow = ControlFlow::Exit;
                        }
                    }
                }
                ToStateMachine::Quit => {
                    debug!("State machine seems to be done, bye from frontend!");
                    app.quit();
                }
                ToStateMachine::SleepUntil(_instant) => {
                    // Select the earliest wakeup time
                    // TODO
                    // next_wakeup = next_wakeup
                    //     .map_or(Some(instant), |before| Some(before.min(instant)));
                }
                ToStateMachine::Click {
                    window_id,
                    x,
                    y,
                    button,
                } => {
                    let start = Instant::now();
                    let mut state_machine = (*state_machine).borrow_mut();
                    let scene_id = *state_machine
                        .root_scenes
                        .bimap_get_by_right(&window_id)
                        .unwrap();
                    let last_scene_size = state_machine
                        .root_scenes
                        .hashmap_get_by_left(&scene_id)
                        .unwrap()
                        .last_scene_size;

                    state_machine.handle_click(
                        scene_id,
                        last_scene_size.0 as i64,
                        last_scene_size.1 as i64,
                        x,
                        y,
                        button,
                    );
                    trace!(window_id, scene_id, "[{:?}] Handled click", start.elapsed());
                }
                ToStateMachine::AllocWindow(scene_id) => {
                    let window_id = window_counter.fetch_add(1, Ordering::SeqCst);
                    trace!(window_id, scene_id, "Allocated window for scene");
                    (*state_machine)
                        .borrow_mut()
                        .register_window_for_scene(scene_id, window_id);

                    let mut windows = windows.borrow_mut();
                    let window_state = WindowState::new(
                        &app,
                        renderer.clone(),
                        state_machine.clone(),
                        wakeup_manager.clone(),
                        window_id,
                        scene_id,
                    );
                    let (scene_size, scene_title) = {
                        let state_machine = &mut (*state_machine).borrow_mut();
                        (
                            WindowFrontend::get_scene_size(state_machine, scene_id),
                            WindowFrontend::get_scene_title(state_machine, scene_id),
                        )
                    };
                    // FIXME: Ugh gtk why do you make me do this
                    const HEADERBAR_SIZE: i32 = 47;
                    window_state.win.set_title(Some(&scene_title));
                    window_state
                        .win
                        .set_default_size(scene_size.0, scene_size.1 + HEADERBAR_SIZE);
                    window_state.win.show();
                    windows.insert(window_id, window_state);
                }
                ToStateMachine::MountExternalWidget {
                    scene_id,
                    texture_metadata,
                    texture_fd,
                } => {
                    info!(scene_id, "Mounting external widget");
                    let mut state_machine = (*state_machine).borrow_mut();
                    let scene_state = &mut state_machine.scenes.get_mut(&scene_id).unwrap().1;
                    scene_state.scene_replacement = SceneReplacement::PendingExternalWidget {
                        texture_metadata,
                        texture_fd,
                    };
                }
            }
            Continue(true)
        });

        application.connect_activate(|_app| {
            debug!("Activated by gtk");
        });

        application.connect_shutdown(|_app| {
            debug!("Shutdown by gtk");
        });

        // Don't quit the app even though it has no windows
        let _hold = application.hold();

        application.run_with_args::<&str>(&[]);
        debug!("app done");
        std::process::exit(0);
    }
}

impl WindowFrontend {
    fn get_scene_size(state_machine: &mut StateMachine, scene_id: SceneId) -> (i32, i32) {
        // Get window size
        const DEFAULT_WINDOW_SIZE: (i32, i32) = (1280, 720);
        state_machine
            .get_default_window_size_for_scene(scene_id)
            .unwrap_or(DEFAULT_WINDOW_SIZE)
    }

    fn get_scene_title(state_machine: &mut StateMachine, scene_id: SceneId) -> String {
        // Get window size
        state_machine
            .get_window_title_for_scene(scene_id)
            .unwrap_or_else(|| "Window".to_string())
    }
}

struct WakeupManager {
    state_machine: Rc<RefCell<StateMachine>>,
    curr_timer: Option<SourceId>,
    next_wakeup: f64,
}

impl WakeupManager {
    pub fn new(state_machine: Rc<RefCell<StateMachine>>) -> Rc<RefCell<Self>> {
        Rc::new(RefCell::new(Self {
            state_machine,
            curr_timer: None,
            next_wakeup: f64::INFINITY,
        }))
    }
}

trait _WakeupManagerHelper {
    fn update_next_wakeup(&self);
    fn select_next(&self);
}

impl _WakeupManagerHelper for Rc<RefCell<WakeupManager>> {
    fn update_next_wakeup(&self) {
        let mut this_ref = (**self).borrow_mut();
        let state_machine = (*this_ref.state_machine).borrow_mut();
        let next_wakeup = *state_machine
            .wakeups
            .descending_values()
            .next()
            .unwrap_or(&f64::INFINITY);
        drop(state_machine);
        if this_ref.next_wakeup != next_wakeup {
            trace!("requested wakeup at {}", next_wakeup);
            this_ref.next_wakeup = next_wakeup;
            drop(this_ref);
            self.select_next();
        }
    }

    fn select_next(&self) {
        let mut this_ref = (**self).borrow_mut();
        this_ref.next_wakeup = f64::INFINITY;

        // Cancel current timer
        if let Some(curr_timer) = this_ref.curr_timer.take() {
            curr_timer.remove();
        }

        // Run all expired wakeups, and schedule next wakeup
        loop {
            let mut state_machine = (*this_ref.state_machine).borrow_mut();
            let current_time = state_machine.timebase.elapsed().as_secs_f64();
            let wakeup = state_machine
                .wakeups
                .descending_items()
                .next()
                .map(|w| (*w.0, *w.1));
            if let Some((scene_id, wakeup_time)) = wakeup {
                if current_time >= wakeup_time {
                    // Already need to wake up
                    state_machine.wakeups.remove(&scene_id);
                    if let Some(&window_id) = state_machine.root_scenes.bimap_get_by_left(&scene_id)
                    {
                        state_machine
                            .event_proxy
                            .as_ref()
                            .unwrap()
                            .to_state_machine(ToStateMachine::Redraw { window_id });
                    }
                    // We want to trigger any remaining redraws, keep on going
                    continue;
                } else if wakeup_time.is_finite() {
                    // Schedule next wakeup
                    let this_clone = self.clone();
                    drop(state_machine);
                    this_ref.curr_timer = Some(glib::timeout_add_local_once(
                        Duration::from_secs_f64(wakeup_time - current_time),
                        move || {
                            trace!("woke up");
                            this_clone.select_next();
                        },
                    ));
                }
            }
            // We're done for now, go away
            break;
        }
    }
}
