import os, math
import platform as platformModule
import time as timeModule

import pygame
from pygame import *
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from Resource import ResourceManager
from Core import *
from Render import *
from Shader import *
from Object import ObjectManager, DebugLine
from Utilities import *


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


class Renderer(Singleton):
    def __init__(self):
        self.width = 0
        self.height = 0
        self.viewportRatio = 1.0
        self.perspective = np.eye(4, dtype=np.float32)
        self.ortho = np.eye(4, dtype=np.float32)
        self.viewMode = GL_FILL
        # managers
        self.coreManager = None
        self.resourceManager = None
        self.objectManager = None
        # console font
        self.console = None
        # components
        self.camera = None
        self.lastShader = None
        self.screen = None
        # TEST_CODE
        self.sceneConstantBuffer = None

    def initScreen(self):
        self.width, self.height = config.Screen.size
        # It's have to pygame set_mode at first.
        self.screen = pygame.display.set_mode((self.width, self.height),
                                              OPENGL | DOUBLEBUF | RESIZABLE | HWPALETTE | HWSURFACE)

    @staticmethod
    def destroyScreen():
        # destroy
        pygame.display.quit()

    def initialize(self, coreManager):
        logger.info("Initialize Renderer")
        self.coreManager = coreManager
        self.resourceManager = ResourceManager.ResourceManager.instance()
        self.objectManager = ObjectManager.instance()

        # console font
        self.console = Console()
        self.console.initialize(self)

        # set gl hint
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

        # Start - fixed pipe line light setting
        glLightfv(GL_LIGHT0, GL_POSITION, (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        # End - fixed pipe line light setting

        # build a scene
        self.resizeScene(self.width, self.height)

        # TEST_CODE : scene constants uniform buffer
        material = self.resourceManager.getMaterial("default")
        self.sceneConstantBuffer = UniformBlock("sceneConstants", material.program)

    def close(self):
        # record config
        config.setValue("Screen", "size", [self.width, self.height])
        config.setValue("Screen", "position", [0, 0])

        # destroy console
        self.console.close()

    def setViewMode(self, viewMode):
        if viewMode == COMMAND.VIEWMODE_WIREFRAME:
            self.viewMode = GL_LINE
        elif viewMode == COMMAND.VIEWMODE_SHADING:
            self.viewMode = GL_FILL

    def resizeScene(self, width, height):
        # It have to pygame set_mode again on Linux.
        if platformModule.system() == 'Linux':
            self.screen = pygame.display.set_mode((self.width, self.height),
                                                  OPENGL | DOUBLEBUF | RESIZABLE | HWPALETTE | HWSURFACE)

        if width <= 0 or height <= 0:
            return

        self.width = width
        self.height = height
        self.viewportRatio = float(width) / float(height)
        self.camera = self.objectManager.getMainCamera()

        # get viewport matrix matrix
        self.perspective = perspective(self.camera.fov, self.viewportRatio, self.camera.near, self.camera.far)
        self.ortho = ortho(0, self.width, 0, self.height, self.camera.near, self.camera.far)

        # set viewport
        glViewport(0, 0, width, height)
        # set perspective view
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.fov, self.viewportRatio, self.camera.near, self.camera.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def renderScene(self):
        # clear buffer
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # render
        self.render_objects()
        self.render_postprocess()

        # render text
        self.console.render()

        # swap buffer
        pygame.display.flip()

    def render_objects(self):
        # set perspective view
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.fov, self.viewportRatio, self.camera.near, self.camera.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # set render state
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)
        glPolygonMode(GL_FRONT_AND_BACK, self.viewMode)

        # TEST_CODE
        light = self.objectManager.lights[0]
        light.transform.setPos((math.sin(timeModule.time()) * 10.0, 0.0, math.cos(timeModule.time()) * 10.0))
        cameraTransform = self.camera.transform

        # TEST_CODE
        self.sceneConstantBuffer.bindData(cameraTransform.matrix.flat, self.perspective.flat,
                                          cameraTransform.pos, FLOAT32_ZERO,
                                          light.transform.getPos(), FLOAT32_ZERO,
                                          light.lightColor)

        # Perspective * View matrix
        vpMatrix = np.dot(cameraTransform.matrix, self.perspective)

        # draw static meshes
        lastMesh = None
        lastProgram = None
        for objList in self.objectManager.renderGroup.values():
            for obj in objList:
                self.render_object(obj, lastProgram, lastMesh, vpMatrix)
                lastProgram = obj.material.program if obj.material else None
                lastMesh = obj.mesh

        """
        # selected object - render additive color
        selected_obj = self.objectManager.getSelectedObject()
        if selected_obj:
            glEnable(GL_BLEND)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            self.render_object(selected_obj, lastProgram, lastMesh, vpMatrix)

            glBlendFunc(GL_ONE, GL_ONE_MINUS_DST_COLOR)
            glLineWidth(1.0)
            glDisable(GL_CULL_FACE)
            glDisable(GL_DEPTH_TEST)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            self.render_object(selected_obj, lastProgram, lastMesh, vpMatrix)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        """

        # reset shader program
        glUseProgram(0)

    @staticmethod
    def render_object(obj, lastProgram, lastMesh, vpMatrix):
        program = obj.material.program
        mesh = obj.mesh

        # bind shader program
        if lastProgram != program:
            glUseProgram(program)
            obj.material.bind()

        # TEST_CODE
        obj.update()
        obj.bind(vpMatrix)

        # At last, bind buffers
        if lastMesh != mesh:
            mesh.bindBuffers()

        mesh.draw()

    def render_postprocess(self):
        # set orthographic view
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # set render state
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDisable(GL_LIGHTING)
