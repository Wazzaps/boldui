import contextlib
import ctypes
import sys
import time

import sdl2
import sdl2.ext
import sdl2.examples.opengl
import skia

from OpenGL import GL

WIDTH, HEIGHT = 1280, 720


def main_loop(state):
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        print(sdl2.SDL_GetError())
        return -1

    window = sdl2.SDL_CreateWindow(b"WindowServer",
                                   sdl2.SDL_WINDOWPOS_CENTERED,
                                   sdl2.SDL_WINDOWPOS_CENTERED, WIDTH, HEIGHT,
                                   sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE)
    if not window:
        print(sdl2.SDL_GetError())
        return -1

    context = sdl2.SDL_GL_CreateContext(window)
    # sdl2.SDL_GL_SetSwapInterval(0)

    event = sdl2.SDL_Event()
    running = True

    last_measurement = time.time()
    fps_counter = 0

    frame_times = 0.0
    frame_counter = 0
    fps_str = ''

    while running:
        with skia_surface(window) as surface:  # type: skia.Surface
            resized = False
            with surface as canvas:  # type: skia.Canvas
                while running and not resized:
                    while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                        if event.type == sdl2.SDL_QUIT:
                            running = False
                            break
                        elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                            state.handle_mouse_down(event.button.x, event.button.y, (surface.width(), surface.height()))
                        elif event.type == sdl2.SDL_MOUSEWHEEL:
                            x = ctypes.c_int()
                            y = ctypes.c_int()
                            sdl2.SDL_GetMouseState(x, y)
                            state.handle_scroll(x.value, y.value, event.wheel.x, event.wheel.y, (surface.width(), surface.height()))
                        elif event.type == sdl2.SDL_WINDOWEVENT:
                            if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
                                # w, h = event.window.data1, event.window.data2
                                # print(f"Resized to {w} x {h}")
                                resized = True

                    if not resized:
                        start = time.time()
                        state.draw(canvas, (surface.width(), surface.height()))

                        # Draw FPS meter
                        fps_paint = skia.Paint(skia.Color(255, 255, 255, 255))
                        fps_font = skia.Font(None, 12)
                        fps_text = fps_str
                        canvas.drawString(fps_text, 6, 16, fps_font, fps_paint)

                        canvas.flush()

                        frame_times += time.time() - start

                        frame_counter += 1
                        fps_counter += 1

                        elapsed = time.time() - last_measurement
                        if elapsed > 0.5:
                            fps = fps_counter / elapsed
                            ft = frame_times / frame_counter * 1000
                            fps_str = f'FPS: {fps:.01f}  FT: {ft:.02f}ms'
                            fps_counter = 0
                            last_measurement = time.time()

                        sdl2.SDL_GL_SwapWindow(window)
                        sdl2.SDL_Delay(1)

    sdl2.SDL_GL_DeleteContext(context)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()
    return 0


@contextlib.contextmanager
def skia_surface(window: sdl2.SDL_Window):
    context = skia.GrDirectContext.MakeGL()
    assert context is not None

    w = ctypes.c_int()
    h = ctypes.c_int()
    sdl2.SDL_GetWindowSize(window, w, h)

    backend_render_target = skia.GrBackendRenderTarget(
        w.value,
        h.value,
        0,  # sampleCnt
        0,  # stencilBits
        skia.GrGLFramebufferInfo(0, GL.GL_RGBA8))
    surface = skia.Surface.MakeFromBackendRenderTarget(
        context, backend_render_target, skia.kBottomLeft_GrSurfaceOrigin,
        skia.kRGBA_8888_ColorType, skia.ColorSpace.MakeSRGB())
    assert surface is not None
    yield surface
    context.abandonContext()
