use crate::renderer::Renderer;
use crate::simulator::Simulator;
use crate::state_machine::WindowId;
use crate::{Frontend, StateMachine, ToStateMachine, PER_FRAME_LOGGING};
use adw::prelude::{ApplicationExt, ApplicationExtManual};
use adw::{Application, HeaderBar};
use boldui_protocol::{A2RUpdate, SceneId};
use glib::{Continue, MainContext, PRIORITY_HIGH};
use gtk::prelude::{BoxExt, GLAreaExt, GtkWindowExt, WidgetExt};
use gtk::{gio, GLArea};
use skia_safe::gpu::gl::FramebufferInfo;
use skia_safe::gpu::{BackendRenderTarget, RecordingContext, SurfaceOrigin};
use skia_safe::{Canvas, Color4f, ColorType, Surface};
use std::collections::HashMap;
use std::ptr;
use std::rc::Rc;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use std::time::Instant;

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
        let (sender, receiver) = MainContext::channel(PRIORITY_HIGH);
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
    win: adw::ApplicationWindow,
    gl_area: GLArea,
}

impl WindowState {
    pub(crate) fn new(
        app: &Application,
        renderer: Rc<Mutex<Renderer>>,
        state_machine: Rc<Mutex<StateMachine>>,
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
            let state_machine = &mut state_machine2.lock().unwrap();

            // Update last scene size
            {
                let window_state = state_machine
                    .root_scenes
                    .hashmap_get_mut_by_left(&scene_id)
                    .unwrap();
                window_state.last_scene_size = (widget.width(), widget.height());
            }

            state_machine.update_and_evaluate(
                scene_id,
                0.0, // TODO: Time value
                widget.width() as i64,
                widget.height() as i64,
            );
            canvas.clear(Color4f::new(0.2, 0.2, 0.2, 1.0));
            renderer
                .lock()
                .unwrap()
                .render_scene(canvas, state_machine, scene_id);
            surface.flush();

            let elapsed_us = start.elapsed().as_micros() as u64;
            total_frametime_us.fetch_add(elapsed_us, Ordering::SeqCst);
            let frame_num = total_frames.fetch_add(1, Ordering::SeqCst);
            min_frametime_us.fetch_min(elapsed_us, Ordering::SeqCst);
            max_frametime_us.fetch_max(elapsed_us, Ordering::SeqCst);
            if frame_num % 100 == 0 {
                println!(
                    "Min: {}us\tAvg: {}us\tMax: {}us",
                    min_frametime_us.load(Ordering::SeqCst),
                    total_frametime_us.load(Ordering::SeqCst) / total_frames.load(Ordering::SeqCst),
                    max_frametime_us.load(Ordering::SeqCst)
                );
            }

            glib::signal::Inhibit(false)
        });

        // let gesture = gtk::Even
        let event_controller = gtk::GestureClick::new();

        event_controller.connect_released(move |_controller, button, x, y| {
            let mut state_machine = state_machine.lock().unwrap();
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

        // Adwaitas' ApplicationWindow does not include a HeaderBar
        let header_bar = HeaderBar::new();
        content.append(&header_bar);
        content.append(&gl_area);
        let win = adw::ApplicationWindow::builder()
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
        let state_machine = Rc::new(Mutex::new(self.state_machine.take().unwrap()));
        let renderer = Rc::new(Mutex::new(self.renderer.take().unwrap()));
        let mut simulator = self.simulator.take();
        let event_recv = self.event_recv.take().unwrap();
        let windows: Mutex<HashMap<u64, WindowState>> = Mutex::new(HashMap::new());
        let window_counter = AtomicU64::new(10);

        let application = Application::builder()
            .application_id("org.boldos.ui.BoldUI")
            .flags(gio::ApplicationFlags::IS_SERVICE)
            .build();

        let app = application.clone();
        event_recv.attach(None, move |event| {
            eprintln!("--- event");
            match event {
                ToStateMachine::Update(A2RUpdate {
                    updated_scenes,
                    run_blocks,
                }) => {
                    let start = Instant::now();
                    state_machine
                        .lock()
                        .unwrap()
                        .update_scenes_and_run_blocks(updated_scenes, run_blocks);
                    eprintln!("[rnd:dbg] A2R update took {:?} to handle", start.elapsed());
                    state_machine
                        .lock()
                        .unwrap()
                        .event_proxy
                        .as_ref()
                        .unwrap()
                        .to_state_machine(ToStateMachine::SimulatorTick { from_update: true });
                }
                ToStateMachine::Redraw { window_id } => {
                    // self.redraw(start);
                    // self.state_machine
                    //     .event_proxy
                    //     .as_ref()
                    //     .unwrap()
                    //     .to_state_machine(ToStateMachine::SimulatorTick { from_update: false });
                    windows
                        .lock()
                        .unwrap()
                        .get(&window_id)
                        .unwrap()
                        .gl_area
                        .queue_draw();
                }
                ToStateMachine::SimulatorTick { from_update } => {
                    if let Some(simulator) = &mut simulator {
                        if let Err(e) =
                            simulator.tick(&mut state_machine.lock().unwrap(), from_update)
                        {
                            eprintln!("[rnd:err] Error while running simulator: {e:?}");
                            app.quit();
                            // *control_flow = ControlFlow::Exit;
                        }
                    }
                }
                ToStateMachine::Quit => {
                    eprintln!("[rnd:ntc] State machine seems to be done, bye from frontend!");
                    app.quit();
                }
                ToStateMachine::SleepUntil(instant) => {
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
                    let mut state_machine = state_machine.lock().unwrap();
                    let scene_id = *state_machine
                        .root_scenes
                        .bimap_get_by_right(&window_id)
                        .unwrap();
                    let last_scene_size = state_machine
                        .root_scenes
                        .hashmap_get_by_left(&scene_id)
                        .unwrap()
                        .last_scene_size;
                    state_machine.update_and_evaluate(
                        scene_id,
                        0.0,
                        last_scene_size.0 as i64,
                        last_scene_size.1 as i64,
                    );
                    // eprintln!("[rnd:dbg] [{:?}] Updated for click", start.elapsed());
                    // TODO: Handle clicks per-scene
                    state_machine.handle_click(
                        scene_id,
                        0.0,
                        last_scene_size.0 as i64,
                        last_scene_size.1 as i64,
                        x,
                        y,
                        button,
                    );
                    // eprintln!("[rnd:dbg] [{:?}] Handled click", start.elapsed());

                    state_machine
                        .event_proxy
                        .as_ref()
                        .unwrap()
                        .to_state_machine(ToStateMachine::Redraw { window_id })
                }
                ToStateMachine::Resize {
                    window_id,
                    width,
                    height,
                } => {
                    // assert_eq!(window_id, 1);
                    // env.windowed_context
                    //     .window()
                    //     .set_inner_size(glutin::dpi::Size::new(glutin::dpi::LogicalSize::new(
                    //         width, height,
                    //     )));
                    // env.surface =
                    //     create_surface(&env.windowed_context, &fb_info, &mut env.gr_context);
                    // env.windowed_context
                    //     .resize(glutin::dpi::PhysicalSize::new(width, height));
                }
                ToStateMachine::AllocWindow(scene_id) => {
                    let window_id = window_counter.fetch_add(1, Ordering::SeqCst);
                    eprintln!("Allocated window #{} for scene #{}", window_id, scene_id);
                    state_machine
                        .lock()
                        .unwrap()
                        .register_window_for_scene(scene_id, window_id);

                    let mut windows = windows.lock().unwrap();
                    let window_state = WindowState::new(
                        &app,
                        renderer.clone(),
                        state_machine.clone(),
                        window_id,
                        scene_id,
                    );
                    let (scene_size, scene_title) = {
                        let state_machine = &mut state_machine.lock().unwrap();
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
            }
            Continue(true)
        });

        application.connect_activate(|app| {
            eprintln!("[rnd:dbg] Activated by gtk");
        });

        application.connect_shutdown(|app| {
            eprintln!("[rnd:dbg] Shutdown by gtk");
        });

        application.run_with_args::<&str>(&[]);
        eprintln!("[rnd:dbg] app done");
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

    fn redraw(
        state_machine: &mut StateMachine,
        scene_id: SceneId,
        renderer: &mut Renderer,
        scene_size: (i32, i32),
        canvas: &mut Canvas,
    ) {
        let start = Instant::now();

        // Create canvas
        // let color_space = ColorSpace::new_srgb();
        // let img_size = ISize::new(scene_size.0, scene_size.1);
        // let image_info = ImageInfo::new_n32(img_size, AlphaType::Unpremul, color_space);
        // let mut surface = Surface::new_raster(&image_info, image_info.min_row_bytes(), None)
        //     .expect("Failed to create surface");
        // let canvas = surface.canvas();
        if PER_FRAME_LOGGING {
            eprintln!("[rnd:dbg] [{:?}] Created canvas", start.elapsed());
        }

        // Render
        canvas.clear(Color4f::new(0.0, 0.0, 0.0, 0.0));
        {
            state_machine.update_and_evaluate(
                scene_id,
                0.0,
                scene_size.0 as i64,
                scene_size.1 as i64,
            );
            if PER_FRAME_LOGGING {
                eprintln!("[rnd:dbg] [{:?}] Updated", start.elapsed());
            }
            renderer.render_scene(canvas, state_machine, scene_id);
            if PER_FRAME_LOGGING {
                eprintln!("[rnd:dbg] [{:?}] Rendered", start.elapsed());
            }
        }
        if PER_FRAME_LOGGING {
            eprintln!("[rnd:dbg] Frame took {:?} to render", start.elapsed());
        }
    }
}
