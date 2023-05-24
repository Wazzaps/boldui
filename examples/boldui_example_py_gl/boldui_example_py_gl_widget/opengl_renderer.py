# Code based on https://github.com/BerkeleyAutomation/meshrender
import os
import numpy as np

os.environ["PYOPENGL_PLATFORM"] = "egl"

from OpenGL.GL import *
from OpenGL.EGL import *

# Create static c_void_p objects to avoid leaking memory
C_VOID_PS = []
for i in range(5):
    C_VOID_PS.append(ctypes.c_void_p(4 * 4 * i))


class OpenGLRenderer(object):
    """An OpenGL 3.0+ renderer, based on PyOpenGL."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._last_width = self.width
        self._last_height = self.height
        # self._vaids = None
        # self._colorbuf, self._depthbuf = None, None
        self._framebuf = None

        # Initialize the OpenGL context
        self.egl_display = None
        self.egl_surface = None
        self.egl_context = None
        self._init_egl()

        # Bind the frame buffer for offscreen rendering
        self._bind_frame_buffer()

        # Use the depth test functionality of OpenGL. Don't clip -- many normals may be backwards.
        # glEnable(GL_DEPTH_TEST)
        # glDepthMask(GL_TRUE)
        # glDepthFunc(GL_LESS)
        # glDepthRange(0.0, 1.0)

        # Load the meshes into VAO's
        # self._buffers = None
        # self._vaids = self._load_meshes()

        # Load the shaders
        # Fix for pyopengl -- bind a framebuffer
        # glBindVertexArray(self._vaids[0])
        # self._full_shader = self._load_shaders(vertex_shader, fragment_shader)
        # self._depth_shader = self._load_shaders(depth_vertex_shader, depth_fragment_shader)
        # glBindVertexArray(0)

    def _init_egl(self):
        from OpenGL.EGL import (
            EGL_SURFACE_TYPE,
            EGL_PBUFFER_BIT,
            EGL_BLUE_SIZE,
            EGL_RED_SIZE,
            EGL_GREEN_SIZE,
            EGL_DEPTH_SIZE,
            EGL_COLOR_BUFFER_TYPE,
            EGL_RGB_BUFFER,
            EGL_HEIGHT,
            EGL_RENDERABLE_TYPE,
            EGL_CONFORMANT,
            EGL_OPENGL_BIT,
            EGL_NONE,
            EGL_DEFAULT_DISPLAY,
            EGL_NO_CONTEXT,
            EGL_WIDTH,
            EGL_OPENGL_API,
            eglGetDisplay,
            eglInitialize,
            eglChooseConfig,
            eglBindAPI,
            eglCreatePbufferSurface,
            eglCreateContext,
            eglMakeCurrent,
            EGLConfig,
        )

        config_attributes = arrays.GLintArray.asArray(
            [
                EGL_SURFACE_TYPE,
                EGL_PBUFFER_BIT,
                EGL_BLUE_SIZE,
                8,
                EGL_RED_SIZE,
                8,
                EGL_GREEN_SIZE,
                8,
                EGL_DEPTH_SIZE,
                24,
                EGL_COLOR_BUFFER_TYPE,
                EGL_RGB_BUFFER,
                EGL_RENDERABLE_TYPE,
                EGL_OPENGL_BIT,
                EGL_CONFORMANT,
                EGL_OPENGL_BIT,
                EGL_NONE,
            ]
        )
        major, minor = ctypes.c_long(), ctypes.c_long()
        num_configs = ctypes.c_long()
        configs = (EGLConfig * 1)()

        # Cache DISPLAY if necessary and get an off-screen EGL display
        orig_dpy = None
        if "DISPLAY" in os.environ:
            orig_dpy = os.environ["DISPLAY"]
            del os.environ["DISPLAY"]
        self.egl_display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
        if orig_dpy is not None:
            os.environ["DISPLAY"] = orig_dpy

        # Initialize EGL
        eglInitialize(self.egl_display, major, minor)
        eglChooseConfig(self.egl_display, config_attributes, configs, 1, num_configs)

        # Bind EGL to the OpenGL API
        eglBindAPI(EGL_OPENGL_API)

        # Create an EGL pbuffer
        self.egl_surface = eglCreatePbufferSurface(
            self.egl_display, configs[0], [EGL_WIDTH, self.width, EGL_HEIGHT, self.height, EGL_NONE]
        )

        # Create an EGL context
        self.egl_context = eglCreateContext(self.egl_display, configs[0], EGL_NO_CONTEXT, None)

        # Make the EGL context current
        eglMakeCurrent(self.egl_display, self.egl_surface, self.egl_surface, self.egl_context)

        self._texture, self._texture_fd, self._texture_metadata = self.export_texture()

    def export_texture(self):
        from OpenGL.EGL import eglCreateImage, EGL_GL_TEXTURE_2D
        from OpenGL.raw.EGL.MESA.image_dma_buf_export import eglExportDMABUFImageQueryMESA, eglExportDMABUFImageMESA

        texture_cell = arrays.GLuintArray.asArray([0])
        assert glGenTextures(1, texture_cell) == 1
        glBindTexture(GL_TEXTURE_2D, texture_cell[0])
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            self.width,
            self.height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            None,
        )
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            0,
            0,
            self.width,
            self.height,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            "\x00" * (self.width * self.height * 4),
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        texture = EGLClientBuffer.from_param(texture_cell[0])
        # texture = EGLClientBuffer.from_param(self.egl_surface)
        image = eglCreateImage(self.egl_display, self.egl_context, EGL_GL_TEXTURE_2D, texture, None)
        assert image

        fourcc = ctypes.c_int()
        num_planes = ctypes.c_int()
        modifiers = ctypes.c_uint64()
        queried = eglExportDMABUFImageQueryMESA(self.egl_display, image, fourcc, num_planes, modifiers)
        assert queried
        assert num_planes.value == 1

        texture_dmabuf_fd = ctypes.c_int()
        stride = ctypes.c_int32()
        offset = ctypes.c_int32()
        exported = eglExportDMABUFImageMESA(self.egl_display, image, texture_dmabuf_fd, stride, offset)
        assert exported

        return (
            texture_cell[0],
            texture_dmabuf_fd.value,
            {
                "fourcc": fourcc.value,
                "modifiers": modifiers.value,
                "stride": stride.value,
                "offset": offset.value,
            },
        )

    def close(self):
        """Destroy the OpenGL context attached to this renderer.

        Warning
        -------
        Once this has been called, the OpenGLRenderer object should be discarded.
        """
        # Delete framebuffers and renderbuffers
        # if self._colorbuf and self._depthbuf:
        #     glDeleteRenderbuffers(2, [self._colorbuf, self._depthbuf])
        #     self._colorbuf = None
        #     self._depthbuf = None

        if self._framebuf:
            glDeleteFramebuffers(1, [self._framebuf])
            self._framebuf = None

        OpenGL.contextdata.cleanupContext()
        from OpenGL.EGL import eglDestroySurface, eglDestroyContext, eglTerminate

        if self.egl_display is not None:
            if self.egl_context is not None:
                eglDestroyContext(self.egl_display, self.egl_context)
                self.egl_context = None
            if self.egl_surface:
                eglDestroySurface(self.egl_display, self.egl_surface)
                self.egl_surface = None
            eglTerminate(self.egl_display)
            self.egl_display = None

    def _bind_frame_buffer(self):
        """Bind the frame buffer for offscreen rendering."""
        # Release the color and depth buffers if they exist:
        if self._framebuf is not None:
            # glDeleteRenderbuffers(2, [self._colorbuf, self._depthbuf])
            glDeleteFramebuffers(1, [self._framebuf])

        # Initialize the Framebuffer into which we will perform off-screen rendering
        # self._colorbuf, self._depthbuf = glGenRenderbuffers(2)
        # glBindRenderbuffer(GL_RENDERBUFFER, self._colorbuf)
        # glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA, self.width, self.height)
        # glBindRenderbuffer(GL_RENDERBUFFER, self._depthbuf)
        # glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height)

        self._framebuf = glGenFramebuffers(1)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._framebuf)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._texture, 0)
        # glFramebufferRenderbuffer(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, self._colorbuf)
        # glFramebufferRenderbuffer(GL_DRAW_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self._depthbuf)

        # Maybe bind to exported fb?
        # glBindTexture(GL_TEXTURE_2D, self._texture)

    def resize(self, width, height):
        """Resize the framebuffer to the given width and height."""
        self.width = width
        self.height = height

    def render(self):
        """Render a color image of the scene."""
        # Reload the frame buffers if the width or height of the camera changed
        if self.width != self._last_width or self.height != self._last_height:
            self._last_width = self.width
            self._last_height = self.height
            self._bind_frame_buffer()

        # glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._framebuf)
        glViewport(0, 0, self.width, self.height)

        glClearColor(0.5, 0.1, 0.1, 1)
        glClear(GL_COLOR_BUFFER_BIT)

        self.scene()

        glFlush()
        # eglCopyBuffers(self.egl_display, self.egl_surface, EGLNativePixmapType.from_param(self._texture))

        # pixels = self.read_pixels()
        from PIL.Image import Image

        # open("image.txt", "wb").write(pixels)
        # Image.fromarray(pixels).save(f"image.png")

    def read_pixels(self):
        # Extract the color buffer
        glBindFramebuffer(GL_READ_FRAMEBUFFER, self._framebuf)
        color_buf = glReadPixels(0, 0, self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE)

        # Re-format it into a numpy array
        # color_im = np.frombuffer(color_buf, dtype=np.uint8).reshape((self.height, self.width, 3))
        # color_im = np.flip(color_im, axis=0)

        return color_buf

    def scene(self):
        pass

    def __del__(self):
        self.close()
