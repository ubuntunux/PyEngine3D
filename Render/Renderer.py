import os

import pygame
from pygame import *
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

from Core import logger, config
from Object import ObjectManager, DebugLine
from Render import *
from Utilities import *


#------------------------------#
# CLASS : Console
#------------------------------#
class Console:
    def __init__(self):
        self.infos = []
        self.debugs = []
        self.renderer = None
        self.texture = None
        self.font = None
        self.enable = True

    def initialize(self, renderer):
        self.renderer = renderer
        self.font = GLFont(defaultFontFile, 12, margin=(10, 0))

    def close(self):
        pass

    def clear(self):
        self.infos = []

    def toggle(self):
        self.enable = not self.enable

    # just print info
    def info(self, text):
        if self.enable:
            self.infos.append(text)

    # debug text - print every frame
    def debug(self, text):
        if self.enable:
            self.debugs.append(text)

    def render(self):
        if self.enable and self.infos:
            text = '\n'.join(self.infos) if len(self.infos) > 1 else self.infos[0]
            if text:
                # render
                self.font.render(text, 0, self.renderer.height - self.font.height)
            self.infos = []

#------------------------------#
# CLASS : Renderer
#------------------------------#
class Renderer(Singleton):
    def __init__(self):
        self.width = 0
        self.height = 0
        self.viewportRatio = 1.0
        self.perspective = np.eye(4,dtype=np.float32)
        self.ortho = np.eye(4,dtype=np.float32)

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
        # shader delete
        self.shaderManager.close()

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

        # get viewport matrix matrix
        self.perspective = perspective(self.camera.fov, self.viewportRatio, self.camera.near, self.camera.far)
        self.ortho = ortho(0, self.width, 0, self.height, self.camera.near, self.camera.far)

        # set viewport
        glViewport(0, 0, width, height)

    # render meshes
    def render_meshes(self):
        # set render state
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)

        # draw Objects
        for obj in self.objectManager.getObjectList():
            obj.draw(self.camera.matrix, self.perspective)

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
        # clear buffer
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # render
        self.render_meshes()
        self.render_postprocess()

        # render text
        self.console.render()

        # swap buffer
        pygame.display.flip()

