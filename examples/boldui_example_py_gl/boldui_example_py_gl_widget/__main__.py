import struct

import boldui.utils
from opengl_renderer import OpenGLRenderer
import colorsys
import time
from OpenGL.GL import *
from PIL import Image
from boldui import BoldUIExternalApp


print("Imports successful!")


# ----------------------


class MyBoldUIExternalApp(BoldUIExternalApp):
    def __init__(self, renderer: OpenGLRenderer):
        self.renderer = renderer
        super().__init__()

    def create_texture(self) -> (int, bytes):
        fd, metadata = self.renderer._texture_fd, self.renderer._texture_metadata
        # fd, metadata = self.renderer.export_texture()
        metadata = struct.pack(
            "<iQIIII",
            metadata["fourcc"],
            metadata["modifiers"],
            metadata["stride"],
            metadata["offset"],
            self.renderer.width,
            self.renderer.height,
        )
        return fd, metadata


class MyRenderer(OpenGLRenderer):
    def scene(self):
        angle = (time.time() * 100) % 360

        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        # "Iterate"
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, self.width, 0.0, self.height, 0.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Draw the squares
        for i in range(5):
            local_angle = (angle + i * 18) % 360
            color = colorsys.hsv_to_rgb(((time.time() + i / 2.0) / 5.0) % 1.0, 1.0, 0.5 + i / 10.0)
            glTranslate(150, 150, 0, 1)
            glRotatef(local_angle, 0, 0, 1)
            glTranslate(-150, -150, 0, 1)
            glColor3f(*color)  # Set the color to blue
            glBegin(GL_QUADS)  # Begin the sketch
            glVertex2f(100, 100)  # Coordinates for the bottom left point
            glVertex2f(200, 100)  # Coordinates for the bottom right point
            glVertex2f(200, 200)  # Coordinates for the top right point
            glVertex2f(100, 200)  # Coordinates for the top left point
            glEnd()  # Mark the end of drawing
            glTranslate(150, 150, 0, 1)
            glRotatef(-local_angle, 0, 0, 1)
            glTranslate(-150, -150, 0, 1)


def main():
    renderer = MyRenderer(512, 512)
    app = MyBoldUIExternalApp(renderer)
    app.setup_logging()
    app.main_loop()
    # t = time.time()
    # frames = 5
    # for i in range(frames):
    #     renderer.render()
    #     # pixels = renderer.read_pixels()
    #     # Image.fromarray(pixels).save(f"image{i}.png")
    # print(1 / ((time.time() - t) / frames), "fps")
    renderer.close()


if __name__ == "__main__":
    main()
