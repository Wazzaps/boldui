use crate::util::{any_as_u8_slice_mut, u8_slice_as_any};
use crate::{EventLoopProxy, SerdeSender, ToStateMachine};
use boldui_protocol::{bincode, EA2RMessage, SceneId, R2EA_MAGIC};
use command_fds::CommandFdExt;
use command_fds::FdMapping;
use nix::libc::intptr_t;
use skia_bindings::{
    GrEGLClientBuffer, GrEGLContext, GrEGLDisplay, GrEGLImage, GrEGLenum, GrGLenum, GrGLuint,
    GrMipmapped,
};
use skia_safe::gpu::gl::TextureInfo;
use skia_safe::gpu::BackendTexture;
use std::collections::HashMap;
use std::fs::File;
use std::io::{IoSliceMut, Read, Write};
use std::mem::size_of;
use std::os::fd::{AsRawFd, OwnedFd, RawFd};
use std::os::unix::net::{AncillaryData, SocketAncillary};
use std::process::Command;
use std::ptr::null_mut;
use tracing::{debug, info};

pub(crate) type RequestId = u32;

#[allow(non_camel_case_types)]
#[derive(Default, Debug, Clone)]
#[repr(C, packed)]
pub struct TextureStorageMetadata {
    fourcc: std::ffi::c_int,
    modifiers: u64,
    stride: i32,
    offset: i32,
    width: u32,
    height: u32,
}

pub struct ExternalApp {
    child: std::process::Child,
    pub sock: std::os::unix::net::UnixStream,
    pending_requests: HashMap<RequestId, SceneId>,
    request_counter: RequestId,
}

impl ExternalApp {
    pub fn spawn(cmd: &str) -> Self {
        info!("spawning external app: {}", cmd);
        let (sock, child_sock) = std::os::unix::net::UnixStream::pair().unwrap();
        let mut command = Command::new("python");
        // FIXME
        command.args(&["boldui_example_py_gl_widget"]);
        command.current_dir("/home/david/code/bold/boldui/examples/boldui_example_py_gl");
        command
            .fd_mappings(vec![
                // Map this process's stdin as FD 0 in the child process.
                FdMapping {
                    parent_fd: 0,
                    child_fd: 0,
                },
                // Map this process's stdout as FD 0 in the child process.
                FdMapping {
                    parent_fd: 1,
                    child_fd: 1,
                },
                // Map this process's stderr as FD 0 in the child process.
                FdMapping {
                    parent_fd: 2,
                    child_fd: 2,
                },
                // Map `child_sock` as FD 3 in the child process.
                FdMapping {
                    parent_fd: child_sock.as_raw_fd(),
                    child_fd: 3,
                },
            ])
            .unwrap();

        // Spawn the child process.
        Self {
            child: command.spawn().unwrap(),
            sock,
            pending_requests: HashMap::new(),
            request_counter: 0,
        }
    }

    // TODO: Make async?
    pub fn connect(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        debug!("connecting to external app");

        // Send hello
        {
            self.sock.write_all(R2EA_MAGIC)?;
            self.sock
                .write_all(&bincode::serialize(&boldui_protocol::R2EAHello {
                    min_protocol_major_version: boldui_protocol::LATEST_EA_MAJOR_VER,
                    min_protocol_minor_version: boldui_protocol::LATEST_EA_MINOR_VER,
                    max_protocol_major_version: boldui_protocol::LATEST_EA_MAJOR_VER,
                    extra_len: 0, // No extra data
                })?)?;
            self.sock.flush()?;
        }

        // Get hello response
        {
            debug!("reading hello response");
            let mut magic = [0u8; boldui_protocol::EA2R_MAGIC.len()];
            self.sock.read_exact(&mut magic).unwrap();
            assert_eq!(&magic, boldui_protocol::EA2R_MAGIC, "Missing magic");

            let hello_res =
                bincode::deserialize_from::<_, boldui_protocol::EA2RHelloResponse>(&mut self.sock)?;

            assert_eq!(
                (
                    hello_res.protocol_major_version,
                    hello_res.protocol_minor_version
                ),
                (
                    boldui_protocol::LATEST_EA_MAJOR_VER,
                    boldui_protocol::LATEST_EA_MINOR_VER
                ),
                "Incompatible version"
            );
            assert_eq!(
                hello_res.extra_len, 0,
                "This protocol version specifies no extra data"
            );

            if let Some(err) = hello_res.error {
                panic!("An error has occurred: code {}: {}", err.code, err.text);
            }
            debug!("connected!");
        }
        Ok(())
    }

    pub fn open(
        &mut self,
        scene_id: SceneId,
        path: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        debug!("opening path in external app: {}", path);
        self.sock.send_with_u32(
            &boldui_protocol::R2EAMessage::Open(boldui_protocol::R2EAOpen {
                path: path.to_string(),
            }),
            // Request ID
            self.request_counter,
        )?;
        self.pending_requests.insert(self.request_counter, scene_id);
        self.request_counter += 1;
        Ok(())
    }

    pub(crate) fn attach_remote_texture(
        metadata: &TextureStorageMetadata,
        texture_dmabuf_fd: OwnedFd,
    ) -> BackendTexture {
        let display = get_egl_display();
        assert!(!display.is_null());

        let attr_list: [EGLAttrib; 17] = [
            EGL_WIDTH,
            metadata.width as EGLAttrib,
            EGL_HEIGHT,
            metadata.height as EGLAttrib,
            EGL_LINUX_DRM_FOURCC_EXT,
            metadata.fourcc as EGLAttrib,
            EGL_DMA_BUF_PLANE0_FD_EXT,
            // We still want the fd to be closed at the end of the block, so we use `as_raw_fd` instead of `into_raw_fd`
            texture_dmabuf_fd.as_raw_fd() as EGLAttrib,
            EGL_DMA_BUF_PLANE0_OFFSET_EXT,
            metadata.offset as EGLAttrib,
            EGL_DMA_BUF_PLANE0_PITCH_EXT,
            metadata.stride as EGLAttrib,
            EGL_DMA_BUF_PLANE0_MODIFIER_LO_EXT,
            metadata.modifiers as u32 as EGLAttrib,
            EGL_DMA_BUF_PLANE0_MODIFIER_HI_EXT,
            (metadata.modifiers >> 32) as u32 as EGLAttrib,
            EGL_NONE,
        ];

        let image = unsafe {
            eglCreateImage(
                display,
                null_mut(),
                EGL_LINUX_DMA_BUF_EXT,
                null_mut(),
                attr_list.as_ptr(),
            )
        };
        assert!(!image.is_null());

        unsafe {
            let mut texture: GrGLuint = 0;
            gl::GenTextures(1, &mut texture);
            gl::BindTexture(GL_TEXTURE_2D, texture);
            glEGLImageTargetTexture2DOES(GL_TEXTURE_2D, image);

            let texture_info = TextureInfo {
                target: GL_TEXTURE_2D,
                id: texture,
                format: GR_GL_RGBA8,
            };
            // dbg!(GrGLFormat::RGBA8.as_gl_format());
            // dbg!(GrGLFormat::from(texture_info.format).as_gl_format());
            let backend_texture = BackendTexture::new_gl(
                (metadata.width as i32, metadata.height as i32),
                GrMipmapped::No,
                texture_info,
            );

            backend_texture
        }
    }

    pub(crate) fn handle_message(
        &mut self,
        request_id: RequestId,
        msg: EA2RMessage,
        fd: Option<OwnedFd>,
        event_loop_proxy: &(dyn EventLoopProxy + Send),
    ) -> Result<(), Box<dyn std::error::Error>> {
        match msg {
            EA2RMessage::UpdateHandled => {}
            EA2RMessage::CreatedExternalWidget { texture_info } => {
                let fd = fd.ok_or("Missing texture fd")?;
                let scene_id = self.pending_requests[&request_id];
                let metadata: &TextureStorageMetadata = unsafe { u8_slice_as_any(&texture_info) };
                event_loop_proxy.to_state_machine(ToStateMachine::MountExternalWidget {
                    scene_id,
                    texture_metadata: metadata.clone(),
                    texture_fd: fd,
                });
            }
            EA2RMessage::SpontaneousUpdate => {}
            EA2RMessage::Error(e) => panic!("Got error from external app: {:?}", e),
        }
        Ok(())
    }
}

impl AsRawFd for ExternalApp {
    fn as_raw_fd(&self) -> RawFd {
        self.sock.as_raw_fd()
    }
}

// fn get_remote_texture_fd() -> Option<(RawFd, texture_storage_metadata_t)> {
//     let mut metadata = texture_storage_metadata_t::default();
//     let mut sa_buf = Vec::new();
//     sa_buf.resize(256, 0u8);
//     let mut sa = SocketAncillary::new(sa_buf.as_mut_slice());
//     eprintln!("2");
//     unsafe {
//         sock.recv_vectored_with_ancillary(
//             &mut [IoSliceMut::new(any_as_u8_slice_mut(&mut metadata))],
//             &mut sa,
//         )
//         .unwrap();
//         eprintln!("3");
//         match sa.messages().next().unwrap().unwrap() {
//             AncillaryData::ScmRights(mut r) => {
//                 let fd = r.next().unwrap();
//                 eprintln!("FD = {:?}", fd);
//                 return Some((fd, metadata));
//             }
//             AncillaryData::ScmCredentials(_) => {
//                 eprintln!("got creds wtf");
//             }
//         }
//         eprintln!("4");
//     }
//     None
// }

type EGLAttrib = intptr_t;

extern "C" {
    fn eglGetCurrentDisplay() -> GrEGLDisplay;
    fn eglCreateImage(
        dpy: GrEGLDisplay,
        ctx: GrEGLContext,
        target: GrEGLenum,
        buffer: GrEGLClientBuffer,
        attrib_list: *const EGLAttrib,
    ) -> GrEGLImage;
}

fn get_egl_display() -> GrEGLDisplay {
    unsafe { eglGetCurrentDisplay() }
}

const EGL_HEIGHT: EGLAttrib = 0x3056;
const EGL_NONE: EGLAttrib = 0x3038;
const EGL_WIDTH: EGLAttrib = 0x3057;
const EGL_LINUX_DMA_BUF_EXT: GrEGLenum = 0x3270;
const EGL_LINUX_DRM_FOURCC_EXT: EGLAttrib = 0x3271;
const EGL_DMA_BUF_PLANE0_FD_EXT: EGLAttrib = 0x3272;
const EGL_DMA_BUF_PLANE0_OFFSET_EXT: EGLAttrib = 0x3273;
const EGL_DMA_BUF_PLANE0_PITCH_EXT: EGLAttrib = 0x3274;

const EGL_DMA_BUF_PLANE0_MODIFIER_LO_EXT: EGLAttrib = 0x3443;
const EGL_DMA_BUF_PLANE0_MODIFIER_HI_EXT: EGLAttrib = 0x3444;

const GL_TEXTURE_2D: u32 = 0x0DE1;
const GR_GL_RGBA8: GrGLenum = 0x8058;

extern "C" {
    // fn glGenTextures(target: GrGLenum, image: GrEGLImage);
    fn glEGLImageTargetTexture2DOES(target: GrGLenum, image: GrEGLImage);
}
