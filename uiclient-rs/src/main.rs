pub(crate) mod render;
pub(crate) mod scene;
pub(crate) mod utils;

use crate::render::UIClient;
use glutin::dpi::PhysicalPosition;
use glutin::event::ElementState;

fn main() {
    use gl::types::*;
    // use gl_rs as gl;
    use glutin::{
        event::{Event, KeyboardInput, VirtualKeyCode, WindowEvent},
        event_loop::{ControlFlow, EventLoop},
        window::WindowBuilder,
        GlProfile,
    };
    use skia_safe::{
        gpu::{gl::FramebufferInfo, BackendRenderTarget, SurfaceOrigin},
        ColorType, Surface,
    };
    use std::convert::TryInto;

    type WindowedContext = glutin::ContextWrapper<glutin::PossiblyCurrent, glutin::window::Window>;

    let el = EventLoop::new();
    let wb = WindowBuilder::new().with_title("rust-skia-gl-window");

    let cb = glutin::ContextBuilder::new()
        .with_srgb(false)
        .with_depth_buffer(0)
        .with_stencil_buffer(8)
        .with_pixel_format(24, 8)
        .with_gl_profile(GlProfile::Core);

    // #[cfg(not(feature = "wayland"))]
    // let cb = cb.with_double_buffer(Some(true));

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

    windowed_context
        .window()
        .set_min_inner_size(Some(glutin::dpi::Size::new(glutin::dpi::LogicalSize::new(
            100.0, 100.0,
        ))));
    // .set_inner_size(glutin::dpi::Size::new(glutin::dpi::LogicalSize::new(
    //     1280.0, 720.0,
    // )));

    fn create_surface(
        windowed_context: &WindowedContext,
        fb_info: &FramebufferInfo,
        gr_context: &mut skia_safe::gpu::DirectContext,
    ) -> skia_safe::Surface {
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

    let mut uiclient = UIClient::new();
    let mut current_mouse_pos = PhysicalPosition::default();

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
                        uiclient.handle_mouse_down(current_mouse_pos, || {
                            env.windowed_context.window().request_redraw();
                        });
                    }
                }
                WindowEvent::CursorMoved { position, .. } => {
                    current_mouse_pos = position;
                }
                _ => (),
            },
            Event::RedrawRequested(_) => {
                {
                    // let right = (env.surface.width() as f32 - 10.);
                    // let bottom = (env.surface.height() as f32 - 10.);

                    let dimensions = (env.surface.width(), env.surface.height());
                    let canvas = env.surface.canvas();

                    uiclient.draw(canvas, dimensions.0, dimensions.1);

                    // canvas.clear(Color::DARK_GRAY);

                    // let mut paint = Paint::default();
                    // paint.set_anti_alias(true);
                    // paint.set_color(Color::RED);
                    // canvas.draw_rect(Rect::new(10., 10., right, bottom), &paint);

                    // renderer::render_frame(frame % 360, 12, 60, canvas);
                }
                env.surface.canvas().flush();
                env.windowed_context.swap_buffers().unwrap();
            }
            _ => (),
        }
    });
}
