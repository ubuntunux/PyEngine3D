import ctypes
import platform as libPlatform
import sys
import time
import re
import traceback

import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *

from Core import *
from Object import ObjectManager, Triangle, Quad, Cube
from Render import Renderer, ShaderManager, MaterialManager, CameraManager
from Utilities import Singleton


#------------------------------#
# Function : IsExtensionSupported
# NeHe Tutorial Lesson: 45 - Vertex Buffer Objects
#------------------------------#
reCheckGLExtention = re.compile("GL_(.+?)_(.+)")

def IsExtensionSupported (TargetExtension):
    """ Accesses the rendering context to see if it supports an extension.
        Note, that this test only tells you if the OpenGL library supports
        the extension. The PyOpenGL system might not actually support the extension.
    """
    Extensions = glGetString (GL_EXTENSIONS)
    Extensions = Extensions.split ()
    bTargetExtension = str.encode(TargetExtension)
    for extension in Extensions:
        if extension == bTargetExtension:
            break
    else:
        # not found surpport
        msg = "OpenGL rendering context does not support '%s'" % TargetExtension
        logger.error(msg)
        raise BaseException(msg)

    # Now determine if Python supports the extension
    # Exentsion names are in the form GL_<group>_<extension_name>
    # e.g.  GL_EXT_fog_coord
    # Python divides extension into modules
    # g_fVBOSupported = IsExtensionSupported ("GL_ARB_vertex_buffer_object")
    # from OpenGL.GL.EXT.fog_coord import *
    m = re.match(reCheckGLExtention, TargetExtension)
    if m:
        group_name =  m.groups()[0]
        extension_name = m.groups()[1]
    else:
        msg = "GL unsupport error, %s" % TargetExtension
        logger.error(msg)
        raise BaseException(msg)

    extension_module_name = "OpenGL.GL.%s.%s" % (group_name, extension_name)

    try:
        __import__ (extension_module_name)
        logger.info("PyOpenGL supports '%s'" % TargetExtension)
    except:
        msg = 'Failed to import', extension_module_name
        logger.error(msg)
        raise BaseException(msg)
    return True


#------------------------------#
# CLASS : CoreManager
#------------------------------#
class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """
    def __init__(self, cmdQueue, uiCmdQueue, cmdPipe):
        super(CoreManager, self).__init__()
        self.running = False

        # command
        self.cmdQueue = cmdQueue
        self.uiCmdQueue = uiCmdQueue
        self.cmdPipe = cmdPipe

        # timer
        self.fpsLimit = 1.0 / 60.0
        self.fps = 0.0
        self.delta = 0.0
        self.currentTime = 0.0

        # mouse
        self.mousePos = np.zeros(3)
        self.mouseOldPos = np.zeros(3)

        # managers
        self.renderer = Renderer.instance()
        self.cameraManager = CameraManager.instance()
        self.objectManager = ObjectManager.instance()
        self.shaderManager = ShaderManager.instance()
        self.materialManager = MaterialManager.instance()

    def initialize(self):
        # process start
        logger.info('Platform : %s' % libPlatform.platform())
        logger.info("Process Start : %s" % self.__class__.__name__)

        # pygame init
        pygame.init()

        # initalize managers
        self.renderer = Renderer.instance()
        self.renderer.initialize(self)

        # ready to launch - send message to ui
        #PipeSendRecv(self.cmdPipe, CMD_UI_RUN, CMD_UI_RUN_OK)
        self.cmdPipe.send(CMD_UI_RUN)


    def run(self):
        # main loop
        self.update()

        # send a message to close ui
        self.uiCmdQueue.put(CMD_CLOSE_UI)

        # close renderer
        self.renderer.close()

        # save config
        config.save()
        logger.info("Save renderer config file - " + config.getFilename())

        # process stop
        logger.info("Process Stop : %s" % self.__class__.__name__)

        # quit
        pygame.quit()

    def error(self, msg):
        logger.error(msg)
        self.close()

    def close(self):
        self.running = False

    def updateCommand(self):
        while not self.cmdQueue.empty():
            cmd = self.cmdQueue.get()
            if cmd == CMD_CLOSE_APP:
                self.close()


    def updateEvent(self):
        # set pos
        self.mouseOldPos = self.mousePos

        for event in pygame.event.get():
            eventType = event.type
            keydown = pygame.key.get_pressed()

            if eventType == QUIT:
                self.close()
            elif eventType == VIDEORESIZE:
                self.renderer.resizeScene(*event.dict['size'])
            elif eventType == KEYDOWN:
                if keydown[K_ESCAPE]:
                    self.close()
                elif keydown[K_1]:
                    self.renderer.objectManager.addPrimitive(Quad, name="quad", pos=(0,0,0))
                elif keydown[K_2]:
                    self.renderer.objectManager.addPrimitive(Cube, name="cube", pos=(0,0,0), material=self.materialManager.getMaterial('simple'))
            elif eventType == MOUSEMOTION:
                self.mousePos = pygame.mouse.get_pos()

    def updateCamera(self):
        camera = self.cameraManager.getMainCamera()
        camera_speed = config.Camera.velocity * self.delta

        camera.rot[0] += (self.mousePos[1] - self.renderer.height * 0.5) * config.Camera.rotation * self.delta
        camera.rot[1] += (self.mousePos[0] - self.renderer.width * 0.5) * config.Camera.rotation * self.delta

        camera.calculateVectors()

        keydown = pygame.key.get_pressed()
        # update camera transform
        if keydown[K_w]:
            camera.pos += camera.front * camera_speed
        elif keydown[K_s]:
            camera.pos -= camera.front * camera_speed

        if keydown[K_a]:
            camera.pos += camera.right * camera_speed
        elif keydown[K_d]:
            camera.pos -= camera.right * camera_speed

        if keydown[K_q]:
            camera.pos += camera.up * camera_speed
        elif keydown[K_e]:
            camera.pos -= camera.up * camera_speed

        if keydown[K_SPACE]:
            camera.pos.flat = [0,0,-6]
            camera.rot.flat = [0,0,1]

    def update(self):
        self.currentTime = time.time()
        self.running = True
        while self.running:
            currentTime = time.time()
            delta = currentTime - self.currentTime

            if delta < self.fpsLimit:
                continue

            # set timer
            self.currentTime = currentTime
            self.delta = delta
            self.fps = 1.0 / delta

            # update command queue
            self.updateCommand()

            # update keyboard and mouse events
            self.updateEvent()

            # update camera
            self.updateCamera()

            # render scene
            self.renderer.renderScene()