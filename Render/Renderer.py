import os
from ctypes import c_int, c_long, c_char_p, pointer

from OpenGL.GL import *
from OpenGL.GLU import *
from sdl2 import *
from sdl2.sdlttf import *

from Core import logger, config
from Object import ObjectManager
from Render import CameraManager, MaterialManager, ShaderManager, GLFont, defaultFont, SDLText
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
        self.texture = None
        self.texture_width = None
        self.texture_height = None

    def initialize(self, renderer):
        self.renderer = renderer
        self.glfont = GLFont(defaultFont, 12)
        self.infos = []
        self.debugs = []

        color = SDL_Color(255, 255, 255)
        self.texture = self.renderText(b"TTF fonts are cool!", str.encode(os.path.join('Render', 'Glametrix.otf')), color, 64)

    def close(self):
        # free texture
        SDL_DestroyTexture(self.texture)

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

    def renderTexture(self, x, y):
        dst = SDL_Rect(x, y)
        SDL_QueryTexture(self.texture, None, None, self.texture_width, self.texture_height)
        dst.w = self.texture_width.contents.value
        dst.h = self.texture_height.contents.value
        SDL_RenderCopy(self.renderer.sdl_renderer, self.texture, None, dst)

    def renderText(self, message, fontFile, color, fontSize):
        SDL_ClearError()
        font = TTF_OpenFont(fontFile, fontSize)
        if font is None:
            logger.info(SDL_GetError())
            return None

        surf = TTF_RenderText_Blended(font, message, color)

        if surf is None:
            TTF_CloseFont(font)
            logger.info("TTF_RenderText error")
            return None

        self.texture = SDL_CreateTextureFromSurface(self.renderer.sdl_renderer, surf)
        if self.texture is None:
            logger.info("CreateTexture error")
            return None

        #Clean up the surface and font
        SDL_FreeSurface(surf)
        TTF_CloseFont(font)

        # get texture info
        self.texture_width = pointer(c_int(0))
        self.texture_height = pointer(c_int(0))
        SDL_QueryTexture(self.texture, None, None, self.texture_width, self.texture_height)


#------------------------------#
# CLASS : Renderer
#------------------------------#
class Renderer(Singleton):
    def __init__(self):
        self.window = None
        self.sdl_renderer = None
        self.ttf = None
        self.context = None

        self.lastShader = None
        self.width = 0
        self.height = 0
        self.SCREEN_WIDTH = pointer(c_int(0))
        self.SCREEN_HEIGHT = pointer(c_int(0))
        self.viewportRatio = 1.0
        self.camera = None
        self.coreManager = None
        self.cameraManager = CameraManager.instance()
        self.objectManager = ObjectManager.instance()
        self.shaderManager = ShaderManager.instance()
        self.materialManager = MaterialManager.instance()

        # console font
        self.console = Console()

    def initialize(self, coreManager):
        # get manager instance
        self.coreManager = coreManager

        # init window
        logger.info("InitializeGL")
        self.width, self.height = config.Screen.size
        self.window = SDL_CreateWindow(b"OpenGL",
                                   SDL_WINDOWPOS_CENTERED,
                                   SDL_WINDOWPOS_CENTERED, self.width, self.height,
                                   SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE)
        if not self.window:
            logger.info((SDL_GetError()))
            self.coreManager.error("Can't create render windows.")

        # create context
        self.context = SDL_GL_CreateContext(self.window)

        # create sdl renderer
        self.sdl_renderer = SDL_CreateRenderer(self.window, -1, SDL_RENDERER_ACCELERATED)

        # True Type Font Init
        self.ttf = TTF_Init()
        if self.ttf != 0:
            self.coreManager.error(b"TTF_Init error")

        # init console text
        self.console.initialize(self)

        # set gl hint
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

        # Start - fixed pipline light setting
        glLightfv(GL_LIGHT0, GL_POSITION, (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        # End - fixed pipline light setting

        # build a scene
        self.cameraManager.initialize(self)
        self.resizeScene()

        # managers initialize
        self.objectManager.initialize(self)
        self.shaderManager.initialize(self)
        self.materialManager.initialize(self)

    def close(self):
        # record config
        X, Y = pointer(c_int(0)), pointer(c_int(0))
        SDL_GetWindowPosition(self.window, X, Y)
        config.setValue("Screen", "size", [self.width, self.height])
        config.setValue("Screen", "position", [X.contents.value, Y.contents.value])

        # destroy console
        self.console.close()

        # destroy
        SDL_GL_DeleteContext(self.context)
        SDL_DestroyRenderer(self.sdl_renderer)
        SDL_DestroyWindow(self.window)

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
        SDL_RenderClear(self.sdl_renderer)

        # display text
        self.console.info("%.2f fps" % self.coreManager.fps)
        self.console.info("%.2f ms" % (self.coreManager.delta*1000))

        # clear buffer
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # render
        self.render_meshes()
        self.render_postprocess()

        glUseProgram(0)
        self.console.render()
        self.console.clear()

        # sdl font test
        self.console.renderTexture(100, 100)

        # final
        glFlush()
        SDL_GL_SwapWindow(self.window)
        SDL_RenderPresent(self.sdl_renderer)