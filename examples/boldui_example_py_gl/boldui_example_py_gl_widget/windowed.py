import colorsys
import os
import time

# os.environ["PYOPENGL_PLATFORM"] = "egl"
os.environ["PYOPENGL_PLATFORM"] = "osmesa"

from OpenGL.GL import *
from OpenGL.GLUT import *

print("Imports successful!")


def iterate():
    glViewport(0, 0, 1000, 1000)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 1000, 0.0, 1000, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def show_screen():
    angle = (time.time() * 100) % 360
    # noinspection PyBroadException
    try:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Remove everything from screen (i.e. displays all white)
        glLoadIdentity()
        iterate()

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

        glutSwapBuffers()
    except Exception:
        traceback.print_exc()
        glutDestroyWindow(wind)


glutInit()  # Initialize a glut instance which will allow us to customize our window
glutInitDisplayMode(GLUT_RGBA)  # Set the display mode to be colored
glutInitWindowSize(1000, 1000)  # Set the width and height of your window
glutInitWindowPosition(0, 0)  # Set the position at which this windows should appear
wind = glutCreateWindow("OpenGL Coding Practice")  # Give your window a title
glutDisplayFunc(show_screen)  # Tell OpenGL to call the show_screen method continuously
glutIdleFunc(show_screen)  # Draw any graphics or shapes in the show_screen function at all times
glutMainLoop()  # Keeps the window created above displaying/running in a loop
