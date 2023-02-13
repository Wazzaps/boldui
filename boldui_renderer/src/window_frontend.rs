use crate::renderer::Renderer;
use crate::simulator::Simulator;
use crate::{Frontend, StateMachine, ToStateMachine, PER_FRAME_LOGGING};
use boldui_protocol::A2RUpdate;
use glutin::dpi::PhysicalPosition;
use glutin::event::ElementState;
use glutin::event_loop::{EventLoop, EventLoopBuilder};
use skia_safe::{Canvas, Color4f, ColorType, Surface};
use std::time::Instant;

pub(crate) struct WindowFrontend {
    pub el: Option<EventLoop<ToStateMachine>>,
    pub renderer: Option<Renderer>,
    pub state_machine: Option<StateMachine>,
    pub simulator: Option<Simulator>,
}

impl crate::EventLoopProxy for glutin::event_loop::EventLoopProxy<ToStateMachine> {
    fn to_state_machine(&self, event: ToStateMachine) {
        self.send_event(event).unwrap();
    }
}

impl WindowFrontend {
    pub fn new(
        renderer: Renderer,
        mut state_machine: StateMachine,
        simulator: Option<Simulator>,
    ) -> (
        Self,
        Box<glutin::event_loop::EventLoopProxy<ToStateMachine>>,
    ) {
        let el = EventLoopBuilder::with_user_event().build();
        let event_proxy = Box::new(el.create_proxy());
        state_machine.event_proxy = Some(event_proxy.clone());
        (
            Self {
                el: Some(el),
                renderer: Some(renderer),
                state_machine: Some(state_machine),
                simulator,
            },
            event_proxy,
        )
    }
}

impl Frontend for WindowFrontend {
    fn main_loop(&mut self) {
        use gl::types::*;
        use glutin::{
            event::{Event, KeyboardInput, VirtualKeyCode, WindowEvent},
            event_loop::ControlFlow,
            window::WindowBuilder,
            GlProfile,
        };
        use skia_safe::gpu::{gl::FramebufferInfo, BackendRenderTarget, SurfaceOrigin};

        type WindowedContext =
            glutin::ContextWrapper<glutin::PossiblyCurrent, glutin::window::Window>;

        let wb = WindowBuilder::new().with_title("boldui renderer");

        let cb = glutin::ContextBuilder::new()
            .with_srgb(false)
            .with_depth_buffer(0)
            .with_stencil_buffer(8)
            .with_pixel_format(24, 8)
            .with_vsync(true)
            .with_gl_profile(GlProfile::Core);

        // #[cfg(not(feature = "wayland"))]
        // let cb = cb.with_double_buffer(Some(true));

        let mut state_machine = self.state_machine.take().unwrap();
        let mut renderer = self.renderer.take().unwrap();
        let mut simulator = self.simulator.take();
        let el = self.el.take().unwrap();
        let windowed_context = cb.build_windowed(wb, &el).unwrap();

        let windowed_context = unsafe { windowed_context.make_current().unwrap() };
        // let pixel_format = windowed_context.get_pixel_format();

        // println!(
        //     "Pixel format of the window's GL context: {:?}",
        //     pixel_format
        // );

        gl::load_with(|s| windowed_context.get_proc_address(s));

        let mut gr_context = skia_safe::gpu::DirectContext::new_gl(None, None).unwrap();

        let fb_info = {
            let mut fboid: GLint = 0;
            unsafe { gl::GetIntegerv(gl::FRAMEBUFFER_BINDING, &mut fboid) };

            FramebufferInfo {
                fboid: fboid.try_into().unwrap(),
                format: skia_safe::gpu::gl::Format::RGBA8.into(),
            }
        };

        let window = windowed_context.window();
        // window.set_fullscreen(Some(Fullscreen::Borderless(None)));
        window.set_min_inner_size(Some(glutin::dpi::Size::new(glutin::dpi::LogicalSize::new(
            100.0, 100.0,
        ))));
        // window.set_inner_size(glutin::dpi::Size::new(glutin::dpi::LogicalSize::new(
        //     1280.0, 720.0,
        // )));
        // windowed_context.resize(glutin::dpi::PhysicalSize::new(1280, 720));

        fn create_surface(
            windowed_context: &WindowedContext,
            fb_info: &FramebufferInfo,
            gr_context: &mut skia_safe::gpu::DirectContext,
        ) -> Surface {
            let pixel_format = windowed_context.get_pixel_format();
            let size = windowed_context.window().inner_size();
            let backend_render_target = BackendRenderTarget::new_gl(
                (
                    size.width.try_into().unwrap(),
                    size.height.try_into().unwrap(),
                ),
                pixel_format.multisampling.map(|s| s.try_into().unwrap()),
                pixel_format.stencil_bits.try_into().unwrap(),
                *fb_info,
            );
            Surface::from_backend_render_target(
                gr_context,
                &backend_render_target,
                SurfaceOrigin::BottomLeft,
                ColorType::RGBA8888,
                None,
                None,
            )
            .unwrap()
        }

        let surface = create_surface(&windowed_context, &fb_info, &mut gr_context);
        // let sf = windowed_context.window().scale_factor() as f32;
        // surface.canvas().scale((sf, sf));

        // let mut frame = 0;

        // Guarantee the drop order inside the FnMut closure. `WindowedContext` _must_ be dropped after
        // `DirectContext`.
        //
        // https://github.com/rust-skia/rust-skia/issues/476
        struct Env {
            surface: Surface,
            gr_context: skia_safe::gpu::DirectContext,
            windowed_context: WindowedContext,
        }

        let mut env = Env {
            surface,
            gr_context,
            windowed_context,
        };

        // let mut uiclient = UIClient::new();
        let mut current_mouse_pos = PhysicalPosition::default();
        let mut last_frame = Instant::now();
        let mut last_scene_size: (i32, i32) = (0, 0);

        el.run(move |event, _, control_flow| {
            *control_flow = ControlFlow::Wait;

            #[allow(deprecated)]
            match event {
                Event::LoopDestroyed => {}
                Event::WindowEvent { event, .. } => match event {
                    WindowEvent::Resized(physical_size) => {
                        env.surface =
                            create_surface(&env.windowed_context, &fb_info, &mut env.gr_context);
                        env.windowed_context.resize(physical_size)
                    }
                    WindowEvent::CloseRequested => *control_flow = ControlFlow::Exit,
                    WindowEvent::KeyboardInput {
                        input:
                            KeyboardInput {
                                virtual_keycode,
                                modifiers,
                                ..
                            },
                        ..
                    } => {
                        if modifiers.logo() {
                            if let Some(VirtualKeyCode::Q) = virtual_keycode {
                                *control_flow = ControlFlow::Exit;
                            }
                        }
                        env.windowed_context.window().request_redraw();
                    }
                    WindowEvent::MouseInput { state, .. } => {
                        if state == ElementState::Pressed {
                            // state_machine.handle_mouse_down(current_mouse_pos, || {
                            //     env.windowed_context.window().request_redraw();
                            // });
                            state_machine
                                .event_proxy
                                .as_ref()
                                .unwrap()
                                .to_state_machine(ToStateMachine::Click {
                                    x: current_mouse_pos.x,
                                    y: current_mouse_pos.y,
                                    button: 0,
                                })
                        }
                    }
                    WindowEvent::CursorMoved { position, .. } => {
                        current_mouse_pos = position;
                    }
                    _ => (),
                },
                Event::RedrawRequested(_) => {
                    {
                        let canvas = env.surface.canvas();

                        Self::redraw(
                            &mut state_machine,
                            &mut renderer,
                            &mut last_scene_size,
                            canvas,
                        );

                        canvas.flush();
                    }
                    env.windowed_context.swap_buffers().unwrap();

                    // let now = Instant::now();
                    // let framerate = 1.0 / ((now - last_frame).as_millis() as f64 / 1_000.0);
                    // println!("framerate: {}", framerate);
                    // last_frame = now;
                }
                Event::MainEventsCleared => {
                    env.windowed_context.window().request_redraw();
                }
                Event::UserEvent(e) => {
                    match e {
                        ToStateMachine::Update(A2RUpdate {
                            updated_scenes,
                            run_blocks,
                        }) => {
                            let start = Instant::now();
                            state_machine.update_scenes_and_run_blocks(updated_scenes, run_blocks);
                            eprintln!("[rnd:dbg] A2R update took {:?} to handle", start.elapsed());
                            state_machine
                                .event_proxy
                                .as_ref()
                                .unwrap()
                                .to_state_machine(ToStateMachine::SimulatorTick {
                                    from_update: true,
                                });
                        }
                        ToStateMachine::Redraw => {
                            // self.redraw(start);
                            // self.state_machine
                            //     .event_proxy
                            //     .as_ref()
                            //     .unwrap()
                            //     .to_state_machine(ToStateMachine::SimulatorTick { from_update: false });
                        }
                        ToStateMachine::SimulatorTick { from_update } => {
                            if let Some(simulator) = &mut simulator {
                                if let Err(e) = simulator.tick(&mut state_machine, from_update) {
                                    eprintln!("[rnd:err] Error while running simulator: {e:?}");
                                    *control_flow = ControlFlow::Exit;
                                }
                            }
                        }
                        ToStateMachine::Quit => {
                            eprintln!(
                                "[rnd:ntc] State machine seems to be done, bye from frontend!"
                            );
                            *control_flow = ControlFlow::Exit;
                        }
                        ToStateMachine::SleepUntil(instant) => {
                            // Select the earliest wakeup time
                            // TODO
                            // next_wakeup = next_wakeup
                            //     .map_or(Some(instant), |before| Some(before.min(instant)));
                        }
                        ToStateMachine::Click { x, y, button } => {
                            state_machine.update_and_evaluate(
                                0.0,
                                last_scene_size.0 as i64,
                                last_scene_size.1 as i64,
                            );
                            // eprintln!("[rnd:dbg] [{:?}] Updated for click", start.elapsed());
                            // TODO: Handle clicks per-scene
                            if let Some(_root_scene) = state_machine.root_scene {
                                state_machine.handle_click(
                                    // root_scene,
                                    0.0,
                                    last_scene_size.0 as i64,
                                    last_scene_size.1 as i64,
                                    x,
                                    y,
                                    button,
                                );
                            }
                            // eprintln!("[rnd:dbg] [{:?}] Handled click", start.elapsed());
                        }
                    }
                }
                _ => (),
            }
        });
    }
}

impl WindowFrontend {
    fn redraw(
        state_machine: &mut StateMachine,
        renderer: &mut Renderer,
        last_scene_size: &mut (i32, i32),
        canvas: &mut Canvas,
    ) {
        let start = Instant::now();

        // Get window size
        let window_size = {
            const DEFAULT_WINDOW_SIZE: (i32, i32) = (1280, 720);
            state_machine
                .root_scene
                .map(|root_scene| {
                    state_machine
                        .get_default_window_size_for_scene(root_scene)
                        .unwrap_or(DEFAULT_WINDOW_SIZE)
                })
                .unwrap_or(DEFAULT_WINDOW_SIZE)
        };
        *last_scene_size = window_size;

        // Create canvas
        // let color_space = ColorSpace::new_srgb();
        // let img_size = ISize::new(window_size.0, window_size.1);
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
            state_machine.update_and_evaluate(0.0, window_size.0 as i64, window_size.1 as i64);
            if PER_FRAME_LOGGING {
                eprintln!("[rnd:dbg] [{:?}] Updated", start.elapsed());
            }
            match state_machine.root_scene {
                None => {
                    canvas.clear(Color4f::new(0.5, 0.1, 0.1, 1.0));
                }
                Some(root_scene) => {
                    renderer.render_scene(canvas, state_machine, root_scene);
                }
            }
            if PER_FRAME_LOGGING {
                eprintln!("[rnd:dbg] [{:?}] Rendered", start.elapsed());
            }
        }
        if PER_FRAME_LOGGING {
            eprintln!("[rnd:dbg] Frame took {:?} to render", start.elapsed());
        }
    }
}
