import time
ts = te = time.time()

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from Core import coreManager, logger
from Object import objectManager
from Utilities import Singleton
from Render.RenderText import GLFont, defaultFont

#------------------------------#
# CLASS : Renderer
#------------------------------#
class Renderer(Singleton):
    def __init__(self):
        self.inited = False
        self.lastShader = None
        self.window = None
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
        self.inited = True

    def resizeScene(self, width, height):
        if not self.inited or width < 0 or height < 0:
            return

        # resize scene
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, float(width) / float(height), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def on_reshape(self, width, height):
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

    def renderScene(self):
        if not self.inited:
            return

        # clear buffer
        glClearColor(0.0, 0.0, 0.0, 1.0)  # This Will Clear The Background Color To Black
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # render
        self.resizeScene(640, 480)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)

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
        self.on_reshape(640, 480)
        glEnable(GL_BLEND)
        glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDisable(GL_LIGHTING)

        glColor(1,1,1,1)
        glPushMatrix( )
        glTranslate( 0, 480-33, 0 )
        glPushMatrix()
        # render text1
        global ts,te
        te = time.time()
        self.testFont1.render("%.1f" % (1.0 / (te - ts)))
        ts = te
        glTranslate( 10, 100, 0 )
        # render text2
        self.testFont2.render("ABC")
        glPopMatrix( )
        glPopMatrix( )



        # final
        glFlush()
        glutSwapBuffers()

    def update(self):
        glutMainLoop()



#------------------------------#
# Globals
#------------------------------#
renderer = Renderer.instance()
