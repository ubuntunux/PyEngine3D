import os

import pygame
from pygame import *
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

from Core import logger, config
from Object import ObjectManager
from Render import CameraManager, MaterialManager, ShaderManager
from Utilities import Singleton


#------------------------------#
# CLASS : Console
#------------------------------#
class Console:
    def __init__(self):
        self.infos = []
        self.debugs = []
        self.renderer = None

    def initialize(self, renderer):
        self.renderer = renderer
        self.infos = []
        self.debugs = []

    def close(self):
        pass

    def clear(self):
        self.infos = []

    # just print info
    def info(self, text):
        self.infos.append(text)

    # debug text - print every frame
    def debug(self, text):
        self.debugs.append(text)

    def render(self):
        pass



#------------------------------#
# CLASS : Renderer
#------------------------------#
class Renderer(Singleton):
    def __init__(self):
        self.width = 0
        self.height = 0
        self.viewportRatio = 1.0

        # components
        self.camera = None
        self.lastShader = None
        self.screen = None

        # managers
        self.coreManager = None
        self.cameraManager = CameraManager.instance()
        self.objectManager = ObjectManager.instance()
        self.shaderManager = ShaderManager.instance()
        self.materialManager = MaterialManager.instance()

        # console font
        self.console = Console()

        # fonts
        self.char = []
        self.lw = 0
        self.lh = 0

    def initialize(self, coreManager):
        # get manager instance
        self.coreManager = coreManager

        # init window
        logger.info("InitializeGL")
        self.width, self.height = config.Screen.size
        self.screen = pygame.display.set_mode((self.width, self.height), OPENGL|DOUBLEBUF|RESIZABLE|HWPALETTE|HWSURFACE)

        # font init
        pygame.font.init()
        if not pygame.font.get_init():
            self.coreManager.error('Could not render font.')

        defaultFont = pygame.font.Font(os.path.join("Resources", "Fonts", 'UbuntuFont.ttf'), 18)

        for c in range(256):
            s = chr(c)
            try:
                letter_render = defaultFont.render(s, 1, (255,255,255), (0,0,0))
                letter = image.tostring(letter_render, 'RGBA', 1)
                letter_w, letter_h = letter_render.get_size()
                self.char.append((letter, letter_w, letter_h))
            except:
                self.char.append((None, 0, 0))
        self.char = tuple(self.char)
        self.lw = self.char[ord('0')][1]
        self.lh = self.char[ord('0')][2]

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
        self.resizeScene(self.width, self.height)

        # managers initialize
        self.objectManager.initialize(self)
        self.shaderManager.initialize(self)
        self.materialManager.initialize(self)

    def close(self):
        # record config
        config.setValue("Screen", "size", [self.width, self.height])
        config.setValue("Screen", "position", [0, 0])

        # destroy console
        self.console.close()

        # destroy
        pygame.display.quit()

    def resizeScene(self, width, height):
        pygame.display.set_mode((width, height), OPENGL|DOUBLEBUF|RESIZABLE|HWPALETTE|HWSURFACE)

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
        # display text
        #self.console.info("%.2f fps" % self.coreManager.fps)
        #self.console.info("%.2f ms" % (self.coreManager.delta*1000))

        # clear buffer
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # render
        self.render_meshes()
        #self.render_postprocess()

        #glUseProgram(0)
        #self.console.render()
        #self.console.clear()

        # set viewport for font
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, self.width - 1.0, 0.0, self.height - 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # set render state
        #glEnable(GL_BLEND)
        #glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        #glDisable(GL_LIGHTING)

        #glUseProgram(0)

        s = str(123)
        i = 0
        lx = 0
        length = len(s)

        glPushMatrix()
        while i < length:
            glRasterPos2i(100 + lx, 100)
            ch = self.char[ ord( s[i] ) ]
            glDrawPixels(ch[1], ch[2], GL_RGBA, GL_UNSIGNED_BYTE, ch[0])
            lx += ch[1]
            i += 1
        glPopMatrix()

        # swap buffer
        pygame.display.flip()

