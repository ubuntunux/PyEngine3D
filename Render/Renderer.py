from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from Object import ObjectManager
from Utilities import Singleton
from __main__ import logger
def Upon_Click (button, button_state, cursor_x, cursor_y):
	print(button)

#------------------------------#
# CLASS : Renderer
#------------------------------#
class Renderer(Singleton):
    def __init__(self):
        self.init = False
        self.lastShader = None

    def initialize(self):
        glutInit()
        glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH )

        logger.info("InitializeGL :", glGetDoublev(GL_VIEWPORT))

        # set render environment
        glClearColor(0.0, 0.0, 0.0, 0.0)  # This Will Clear The Background Color To Black
        glClearDepth(1.0)  # Enables Clearing Of The Depth Buffer
        glDepthFunc(GL_LESS)  # The Type Of Depth Test To Do
        glEnable(GL_DEPTH_TEST)  # Enables Depth Testing

        glShadeModel(GL_SMOOTH)  # Enables Smooth Color Shading
        glEnable(GL_CULL_FACE)

        # Start - fixed pipline light setting
        glLightfv(GL_LIGHT0, GL_POSITION, (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        # End - fixed pipline light setting

        # initialized flag
        self.init = True

    def resizeScene(self, width, height):
        if not self.init or width < 0 or height < 0:
            return

        # resize scene
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, float(width) / float(height), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def renderScene(self):
        if not self.init:
            return

        # clear buffer
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # render
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(0,0,-6)
        for obj in ObjectManager.getObjectList():
            # set shader
            curShader = obj.material.getShader()
            if self.lastShader != curShader:
                glUseProgram(curShader)
                self.lastShader = curShader
            glPushMatrix()
            glTranslatef(*obj.pos)
            glPopMatrix()
            obj.draw()
        glutSolidSphere(1.0,32,32)
        glutSolidCube( 1.0 )
        glPopMatrix()
        glFlush()


#------------------------------#
# Globals
#------------------------------#
Renderer = Renderer.instance()