import time

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from Core import coreManager, logger
from Object import objectManager
from Utilities import Singleton
from Camera import cameraManager
from Render.RenderText import GLFont, defaultFont


#------------------------------#
# CLASS : Renderer
#------------------------------#
class Renderer(Singleton):
    def __init__(self):
        self.initedViewport= False
        self.lastShader = None
        self.window = None
        self.width = 0
        self.height = 0
        self.viewportRatio = 1.0
        self.camera = None

        # timer
        self.fps = 0.0
        self.delta = 0.0
        self.currentTime = 0.0

        self.testFont1 = None
        self.testFont2 = None
        # regist
        coreManager.regist("Renderer", self)

    def initialize(self):
        glutInit()
        glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH )
        glutInitWindowSize(640, 480)
        glutInitWindowPosition(0, 0)
        self.window = glutCreateWindow(b"GuineaPig")
        glutDisplayFunc(self.renderScene)
        glutIdleFunc(self.renderScene)
        glutReshapeFunc(self.resizeScene)
        glutKeyboardFunc(self.keyPressed)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

        # Start - fixed pipline light setting
        glLightfv(GL_LIGHT0, GL_POSITION, (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        # End - fixed pipline light setting

        # make font
        self.testFont1 = GLFont(defaultFont, 64)
        self.testFont2 = GLFont(defaultFont, 14)

        # initialized flag
        logger.info("InitializeGL : %s" % glGetDoublev(GL_VIEWPORT))

    def resizeScene(self, width, height):
        if width <= 0 or height <= 0:
            return
        self.width = width
        self.height = height
        self.viewportRatio = float(width) / float(height)
        self.camera = cameraManager.getMainCamera()

        # resize scene
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.fov, self.viewportRatio, self.camera.near, self.camera.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.initedViewport = True

    def on_reshape(self, width, height):
        if width <= 0 or height <= 0:
            return

        self.width = width
        self.height = height
        self.viewportRatio = float(self.width) / float(self.height)

        glViewport( 0, 0, width, height )
        glMatrixMode( GL_PROJECTION )
        glLoadIdentity( )
        glOrtho( 0, width, 0, height, -1, 1 )
        glMatrixMode( GL_MODELVIEW )
        glLoadIdentity( )

    def keyPressed(self, *args):
        # If escape is pressed, kill everything.
        if args[0] == '\x1b':
            sys.exit()

    # render meshes
    def render_meshes(self):
        # set perspective view
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.fov, self.viewportRatio, self.camera.near, self.camera.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # set render state
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)

        # render
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(0,0,-6)
        for obj in objectManager.getObjectList():
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

    # draw text
    def render_text(self):
        # set OrthoView
        glMatrixMode( GL_PROJECTION )
        glLoadIdentity( )
        glOrtho( 0, self.width, 0, self.height, -1, 1 )
        glMatrixMode( GL_MODELVIEW )
        glLoadIdentity( )

        # render state
        glEnable(GL_BLEND)
        glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDisable(GL_LIGHTING)

        # render
        glColor(1,1,1,1)
        glPushMatrix( )
        glTranslate( 0, 480-33, 0 )
        glPushMatrix()
        # render text1
        self.testFont1.render("%.1f" % self.fps)
        glTranslate( 10, 100, 0 )
        # render text2
        self.testFont2.render("ABC")
        glPopMatrix( )
        glPopMatrix( )

    def render_postprocess(self):
        pass

    def renderScene(self):
        currentTime = time.time()
        delta = self.currentTime - currentTime

        if not self.initedViewport or delta == 0.0:
            return

        # set timer
        self.currentTime = currentTime
        self.delta = delta
        self.fps = 1.0 / self.delta

        # clear buffer
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # render
        self.render_meshes()
        self.render_postprocess()
        self.render_text()

        # final
        glFlush()
        glutSwapBuffers()

    def update(self):
        glutMainLoop()



#------------------------------#
# Globals
#------------------------------#
renderer = Renderer.instance()
