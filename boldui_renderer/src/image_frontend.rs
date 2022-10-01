use crate::renderer::Renderer;
use crate::StateMachine;
use parking_lot::Mutex;
use skia_safe::{AlphaType, Color4f, ColorSpace, EncodedImageFormat, ISize, ImageInfo, Surface};
use std::fs::File;
use std::io::{BufWriter, Write};
use std::sync::mpsc::{Receiver, Sender};

pub struct ImageFrontend<'a> {
    pub wakeup_recv: Receiver<()>,
    pub renderer: Renderer,
    pub state_machine: &'a Mutex<StateMachine>,
}

pub struct ImageEventLoopProxy {
    pub wakeup_send: Sender<()>,
}

impl ImageEventLoopProxy {
    pub fn request_redraw(&self) {
        self.wakeup_send.send(()).unwrap()
    }
}

impl<'a> ImageFrontend<'a> {
    pub fn new(
        renderer: Renderer,
        state_machine: &'a Mutex<StateMachine>,
    ) -> (ImageFrontend<'a>, ImageEventLoopProxy) {
        let (wakeup_send, wakeup_recv) = std::sync::mpsc::channel();
        (
            Self {
                wakeup_recv,
                renderer,
                state_machine,
            },
            ImageEventLoopProxy { wakeup_send },
        )
    }

    pub fn main_loop(&mut self) {
        // Create canvas
        for i in 0u64.. {
            if self.wakeup_recv.recv().is_err() {
                println!("State machine seems to be done, bye from frontend!");
                break;
            }

            let mut state = self.state_machine.lock();
            let window_size = {
                const DEFAULT_WINDOW_SIZE: (i32, i32) = (1280, 720);
                let root_scene = state.root_scene.unwrap();
                state
                    .get_default_window_size_for_scene(root_scene)
                    .unwrap_or(DEFAULT_WINDOW_SIZE)
            };

            let color_space = ColorSpace::new_srgb();
            let img_size = ISize::new(window_size.0, window_size.1);
            let image_info = ImageInfo::new_n32(img_size, AlphaType::Unpremul, color_space);
            let mut surface = Surface::new_raster(&image_info, image_info.min_row_bytes(), None)
                .expect("Failed to create surface");
            let canvas = surface.canvas();

            // Render
            canvas.clear(Color4f::new(0.0, 0.0, 0.0, 0.0));
            {
                state.update_and_evaluate(0.0, img_size.width as i64, img_size.height as i64);
                self.renderer.render(canvas, &mut *state);
            }

            // Encode it
            let mut out = BufWriter::new(File::create(format!("target/result-{i}.png")).unwrap());
            let img = surface
                .image_snapshot()
                .encode_to_data(EncodedImageFormat::PNG)
                .expect("Failed to encode as PNG");
            out.write_all(img.as_bytes()).expect("Failed to write PNG");
            println!("Wrote frame #{i}");
        }
    }
}
