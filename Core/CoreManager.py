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
from Utilities import *


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
        self.mousePos = np.zeros(2)
        self.mouseOldPos = np.zeros(2)
        self.mouseDelta = np.zeros(2)
        self.wheelUp = False
        self.wheelDown = False

        # managers
        self.renderer = Renderer.instance()
        self.console = self.renderer.console
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
        self.mouseDelta[:] = self.mousePos - self.mouseOldPos
        self.mouseOldPos[:] = self.mousePos
        self.wheelUp, self.wheelDown = False, False

        for event in pygame.event.get():
            eventType = event.type
            if eventType == QUIT:
                self.close()
            elif eventType == VIDEORESIZE:
                self.renderer.resizeScene(*event.dict['size'])
            elif eventType == KEYDOWN:
                keyDown = event.key
                if keyDown == K_ESCAPE:
                    self.close()
                elif keyDown == K_BACKQUOTE:
                    self.console.toggle()
                elif keyDown == K_1:
                    for i in range(100):
                        pos = [np.random.uniform(-10,10) for i in range(3)]
                        primitive = [Triangle, Quad, Cube][np.random.randint(3)]
                        obj = self.renderer.objectManager.addPrimitive(primitive, name="", pos=pos)
                        translate(obj.matrix, *obj.pos)
            elif eventType == MOUSEMOTION:
                self.mousePos[:] = pygame.mouse.get_pos()
            elif eventType == MOUSEBUTTONDOWN:
                self.wheelUp = event.button == 4
                self.wheelDown = event.button == 5

    def updateCamera(self):
        camera = self.cameraManager.getMainCamera()
        camera_speed = camera.pan_speed * self.delta
        camera_rotation = camera.rotation_speed * self.delta

        # get pressed mouse buttons
        btnL, btnM, btnR = pygame.mouse.get_pressed()

        # camera move pan
        if btnL and btnR or btnM:
            translate(camera.matrix, self.mouseDelta[0] * camera_speed * 0.1, -self.mouseDelta[1] * camera_speed * 0.1, 0.0)
        # camera rotation
        elif btnL or btnR:
            yrotate(camera.matrix, -self.mouseDelta[0] * camera_rotation)
            xrotate(camera.matrix, -self.mouseDelta[1] * camera_rotation)
        # camera move front/back
        if self.wheelUp:
            translate(camera.matrix, 0.0, 0.0, camera_speed * 10.0)
        elif self.wheelDown:
            translate(camera.matrix, 0.0, 0.0, -camera_speed * 10.0)


        keydown = pygame.key.get_pressed()
        # update camera transform
        if keydown[K_w]:
            translate(camera.matrix, 0.0, 0.0, camera_speed)
        elif keydown[K_s]:
            translate(camera.matrix, 0.0, 0.0, -camera_speed)

        if keydown[K_a]:
            translate(camera.matrix, camera_speed, 0, 0)
        elif keydown[K_d]:
            translate(camera.matrix, -camera_speed, 0, 0)

        if keydown[K_q]:
            translate(camera.matrix, 0, -camera_speed, 0)
        elif keydown[K_e]:
            translate(camera.matrix, 0, camera_speed, 0)

        if keydown[K_SPACE]:
            camera.initialize()

        # print camera transform
        rows = []
        for row in camera.matrix:
            rows.append(" ".join(["%+2.2f" % i for i in row]))
        rows = "\n".join(rows)
        self.renderer.console.info(rows)


    def update(self):
        self.currentTime = time.time()
        self.running = True
        while self.running:
            currentTime = time.time()
            delta = currentTime - self.currentTime
            updateTime = currentTime

            if delta < self.fpsLimit:
                continue

            # set timer
            self.currentTime = currentTime
            self.delta = delta
            self.fps = 1.0 / delta

            # update
            self.updateCommand() # update command queue
            self.updateEvent() # update keyboard and mouse events
            self.updateCamera() # update camera

            # update time
            updateTime = time.time() - updateTime

            # render scene
            renderTime = time.time()
            self.renderer.renderScene()
            renderTime = time.time() - renderTime

            self.console.info("CPU : %.2f ms" % (updateTime * 1000.0))
            self.console.info("GPU : %.2f ms" % (renderTime * 1000.0))