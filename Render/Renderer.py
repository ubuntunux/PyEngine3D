import time
import os
from ctypes import c_int, c_long, pointer

from OpenGL.GL import *
from OpenGL.GLU import *

from sdl2 import *
# use local sdl library file path
sdlpath = os.path.join(os.path.dirname(__file__), 'libs')
if os.path.exists(sdlpath):
    os.environ['PYSDL2_DLL_PATH'] = sdlpath

from Core import logger, config
from Object import ObjectManager, Quad
from Render import CameraManager, GLFont, defaultFont
from Utilities import Singleton

#------------------------------#
# CLASS : Console
#------------------------------#
class Console:
    def __init__(self):
        self.glfont = None
        self.infos = []
        self.debugs = []
        self.padding = 10
        self.renderer = None

    def initialize(self):
        self.renderer = Renderer.instance()
        self.glfont = GLFont(defaultFont, 12)
        self.infos = []
        self.debugs = []

    def clear(self):
        self.infos = []

    # just print info
    def info(self, text):
        self.infos.append(text)

    # debug text - print every frame
    def debug(self, text):
        self.debugs.append(text)

    def render(self):
        '''
        # set orthographic view
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
        '''

        # render
        glColor(1,1,1,1)
        glPushMatrix( )
        glTranslate( self.padding, self.renderer.height - self.padding, 0 )
        glPushMatrix()
        # render text
        self.glfont.render("\n".join(self.debugs + self.infos))
        glPopMatrix( )
        glPopMatrix( )


#------------------------------#
# CLASS : Renderer
#------------------------------#
class Renderer(Singleton):
    def __init__(self):
        self.inited = False
        self.window = None
        self.context = None
        self.event = None
        self.running = False
        self.lastShader = None
        self.width = 0
        self.height = 0
        self.SCREEN_WIDTH = pointer(c_int(0))
        self.SCREEN_HEIGHT = pointer(c_int(0))
        self.viewportRatio = 1.0
        self.camera = None
        self.coreManager = None
        self.objectManager = None
        self.cameraManager = None

        # timer
        self.fpsLimit = 1.0 / 60.0
        self.fps = 0.0
        self.delta = 0.0
        self.currentTime = 0.0

        # console font
        self.console = Console()

    def initialize(self, coreManager):
        self.coreManager = coreManager
        self.objectManager = ObjectManager.instance()
        self.cameraManager = CameraManager.instance()
        self.initGL()

    def initGL(self):
        self.width, self.height = config.Screen.size
        self.window = SDL_CreateWindow(b"OpenGL demo",
                                   SDL_WINDOWPOS_CENTERED,
                                   SDL_WINDOWPOS_CENTERED, self.width, self.height,
                                   SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE)
        if not self.window:
            logger.info((SDL_GetError()))
            self.close()

        self.context = SDL_GL_CreateContext(self.window)
        self.event = SDL_Event()

        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

        # Start - fixed pipline light setting
        glLightfv(GL_LIGHT0, GL_POSITION, (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        # End - fixed pipline light setting

        self.resizeScene()

        # init console text
        self.console.initialize()

        # initialized flag
        logger.info("InitializeGL : %s" % glGetDoublev(GL_VIEWPORT))

    def close(self):
        self.running = False
        X, Y = pointer(c_int(0)), pointer(c_int(0))
        SDL_GetWindowPosition(self.window, X, Y)
        config.setValue("Screen", "size", [self.width, self.height])
        config.setValue("Screen", "position", [X.contents.value, Y.contents.value])
        SDL_GL_DeleteContext(self.context)
        SDL_DestroyWindow(self.window)
        #SDL_Quit() - run in main.py ( multiprocess error : double free error )

    def resizeScene(self):
        SDL_GetWindowSize(self.window, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        width = self.SCREEN_WIDTH.contents.value
        height = self.SCREEN_HEIGHT.contents.value

        if width <= 0 or height <= 0:
            return

        self.width = width
        self.height = height
        self.viewportRatio = float(width) / float(height)
        self.camera = self.cameraManager.getMainCamera()

        # resize scene
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.fov, self.viewportRatio, self.camera.near, self.camera.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.inited = True

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

        # Transform Camera
        glTranslatef(*self.camera.pos)

        # Transform Objects
        for obj in self.objectManager.getObjectList():
            # set shader
            curShader = obj.material.getShader()
            if self.lastShader != curShader:
                glUseProgram(curShader)
                self.lastShader = curShader

            glPushMatrix()
            glTranslatef(*obj.pos)
            glPopMatrix()
            obj.draw()
        # Pop Camera Transform
        glPopMatrix()

    def render_postprocess(self):
        # set orthographic view
        glMatrixMode( GL_PROJECTION )
        glLoadIdentity( )
        glOrtho( 0, self.width, 0, self.height, -1, 1 )
        glMatrixMode( GL_MODELVIEW )
        glLoadIdentity( )

        # set render state
        glEnable(GL_BLEND)
        glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDisable(GL_LIGHTING)

    def renderScene(self):
        currentTime = time.time()
        delta = currentTime - self.currentTime

        if not self.inited or delta < self.fpsLimit:
            return

        fps = 1.0 / delta

        # update core manager
        self.coreManager.update(currentTime, delta, fps)

        # set timer
        self.currentTime = currentTime
        self.delta = delta
        self.fps = fps
        self.console.info("%.2f fps" % self.fps)
        self.console.info("%.2f ms" % (self.delta*1000))

        # clear buffer
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # render
        self.render_meshes()
        self.render_postprocess()
        self.console.render()
        self.console.clear()

        # final
        glFlush()
        SDL_GL_SwapWindow(self.window)


    def update(self):
        self.objectManager.addPrimitive(Quad, objName='quad', pos=(0,0,0))
        self.running = True
        while self.running:
            while SDL_PollEvent(ctypes.byref(self.event)) != 0:
                if self.event.type == SDL_QUIT:
                    self.running = False
                    self.close()
                elif self.event.type == SDL_WINDOWEVENT:
                    if self.event.window.event == SDL_WINDOWEVENT_RESIZED:
                        self.resizeScene()
            self.renderScene()