#!/usr/bin/env python3

import contextlib
import ctypes
import sys

import sdl2
import sdl2.ext
import sdl2.examples.opengl
import skia

from OpenGL import GL

WIDTH, HEIGHT = 1280, 720


def draw(canvas: skia.Canvas):
    canvas.clear(0xff202020)
    canvas.drawString(
        "Hello, World!", 20, 50, skia.Font(None, 36), skia.Paint(skia.Color(200, 200, 200, 255)))
    canvas.flush()


def create_window():
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        print(sdl2.SDL_GetError())
        return -1

    window = sdl2.SDL_CreateWindow(b"WindowServer",
                                   sdl2.SDL_WINDOWPOS_CENTERED,
                                   sdl2.SDL_WINDOWPOS_CENTERED, WIDTH, HEIGHT,
                                   sdl2.SDL_WINDOW_OPENGL)
    if not window:
        print(sdl2.SDL_GetError())
        return -1

    context = sdl2.SDL_GL_CreateContext(window)

    event = sdl2.SDL_Event()
    running = True
    with skia_surface() as surface:
        with surface as canvas:
            while running:
                while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                    if event.type == sdl2.SDL_QUIT:
                        running = False

                draw(canvas)

                sdl2.SDL_GL_SwapWindow(window)
                sdl2.SDL_Delay(10)
    sdl2.SDL_GL_DeleteContext(context)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()
    return 0


@contextlib.contextmanager
def skia_surface():
    context = skia.GrDirectContext.MakeGL()
    assert context is not None
    backend_render_target = skia.GrBackendRenderTarget(
        WIDTH,
        HEIGHT,
        0,  # sampleCnt
        0,  # stencilBits
        skia.GrGLFramebufferInfo(0, GL.GL_RGBA8))
    surface = skia.Surface.MakeFromBackendRenderTarget(
        context, backend_render_target, skia.kBottomLeft_GrSurfaceOrigin,
        skia.kRGBA_8888_ColorType, skia.ColorSpace.MakeSRGB())
    assert surface is not None
    yield surface
    context.abandonContext()


if __name__ == '__main__':
    sys.exit(create_window())
