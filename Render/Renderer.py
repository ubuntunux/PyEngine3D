from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from Shader import ShaderManager
from Object import ObjectManager, Triangle, Quad
from Utilities import Singleton, getLogger

r =0.0

logger = getLogger('default')

class Renderer(Singleton):
    def __init__(self):
        self.init = False
        self.lastShader = None

        # managers
        self.shaderManager = None
        self.objectManager = None

    def initializeGL(self):
        logger.info("InitializeGL :", glGetDoublev(GL_VIEWPORT))

        # initialize glut
        glutInit()

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

        # initialize managers
        self.shaderManager = ShaderManager()
        self.objectManager = ObjectManager()

        # create object
        self.objectManager.addPrimitive(primitive = Triangle, name = 'Triangle', pos = (-1, 0, -6))
        self.objectManager.addPrimitive(primitive = Quad, name = 'Quad', pos = (1, 0, -6))

        # initialized flag
        self.init = True

    def resizeScene(self, width, height):
        if not self.init or width < 0 or height < 0:
            return

        # resize scene
        logger.info("resize scene")
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
        for obj in self.objectManager.getObjectList():
            # set shader
            curShader = obj.material.getShader()
            if self.lastShader != curShader:
                glUseProgram(curShader)
                self.lastShader = curShader

            # set matrix
            glLoadIdentity()
            glTranslatef(*obj.pos)
            obj.draw()

        global r
        glPushMatrix()
        glRotated(r, 0.0, 1.0, 0.0)
        glutSolidTorus(0.3, 0.5, 30, 30)
        glPopMatrix()
        r += 1.0
        if r > 360.0: r = 0.0
