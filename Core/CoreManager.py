import ctypes
import platform as libPlatform
import sys
import time
import re
import traceback
import threading

import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *

from Core import *
from Resource import ResourceManager
from Object import ObjectManager
from Render import Renderer
from Utilities import *


# Function : IsExtensionSupported
# NeHe Tutorial Lesson: 45 - Vertex Buffer Objects
reCheckGLExtention = re.compile("GL_(.+?)_(.+)")

def IsExtensionSupported(TargetExtension):
    """ Accesses the rendering context to see if it supports an extension.
        Note, that this test only tells you if the OpenGL library supports
        the extension. The PyOpenGL system might not actually support the extension.
    """
    Extensions = glGetString(GL_EXTENSIONS)
    Extensions = Extensions.split()
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
        group_name = m.groups()[0]
        extension_name = m.groups()[1]
    else:
        msg = "GL unsupport error, %s" % TargetExtension
        logger.error(msg)
        raise BaseException(msg)

    extension_module_name = "OpenGL.GL.%s.%s" % (group_name, extension_name)

    try:
        __import__(extension_module_name)
        logger.info("PyOpenGL supports '%s'" % TargetExtension)
    except:
        msg = 'Failed to import', extension_module_name
        logger.error(msg)
        raise BaseException(msg)
    return True


# ------------------------------#
# CLASS : CoreManager
# ------------------------------#
class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """

    def __init__(self, cmdQueue, uiCmdQueue, cmdPipe):
        self.running = False

        # command
        self.cmdQueue = cmdQueue
        self.uiCmdQueue = uiCmdQueue
        self.cmdPipe = cmdPipe

        # timer
        self.fps = 0.0
        self.minDelta = 1.0 / 60.0  # 60fps
        self.delta = 0.0
        self.updateTime = 0.0
        self.logicTime = 0.0
        self.renderTime = 0.0
        self.currentTime = 0.0

        # mouse
        self.mousePos = np.zeros(2)
        self.mouseOldPos = np.zeros(2)
        self.mouseDelta = np.zeros(2)
        self.wheelUp = False
        self.wheelDown = False

        # managers
        self.camera = None
        self.resourceManager = ResourceManager.instance()
        self.renderer = Renderer.instance()
        self.console = self.renderer.console
        self.objectManager = ObjectManager.instance()

    def initialize(self):
        # process start
        logger.info('Platform : %s' % libPlatform.platform())
        logger.info("Process Start : %s" % getClassName(self))

        # ready to launch - send message to ui
        self.cmdPipe.SendAndRecv(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)

        # pygame init
        pygame.init()

        # init screen
        self.renderer.initScreen()

        # initalize managers
        self.resourceManager.initialize()
        self.objectManager.initialize()
        self.renderer.initialize(self)

    def run(self):
        # main loop
        self.update()

        # send a message to close ui
        if self.uiCmdQueue:
            self.uiCmdQueue.put(COMMAND.CLOSE_UI)

        # close renderer
        self.renderer.close()

        # close resource manager
        self.resourceManager.close()

        # destory screen
        self.renderer.destroyScreen()

        # save config
        config.save()
        logger.info("Saved config file - " + config.getFilename())

        # process stop
        logger.info("Process Stop : %s" % getClassName(self))

        # quit
        pygame.quit()

    def error(self, msg):
        logger.error(msg)
        self.close()

    def close(self):
        self.running = False

    # receive and send messages, communication with GUI
    def sendObjectName(self, obj):
        if obj:
            self.uiCmdQueue.put(COMMAND.TRANS_OBJECT_NAME, obj.name)
        else:
            logger.error("Cannot find " + (objName or ""))


    def updateCommand(self):
        """
        process recieved command queues and send datas.
        :return None:
        """
        while not self.cmdQueue.empty():
            # receive value must be tuple type
            cmd, value = self.cmdQueue.get()

            # close app
            if cmd == COMMAND.CLOSE_APP:
                self.close()
                return
                # View mode
            elif COMMAND.VIEWMODE_WIREFRAME.value <= cmd.value <= COMMAND.VIEWMODE_SHADING.value:
                self.renderer.setViewMode(cmd)
            # Resource Message
            elif cmd == COMMAND.ADD_RESOURCE:
                resName, resType = value
                camera = self.objectManager.getMainCamera()
                pos = camera.pos + camera.front * 10.0
                mesh = self.resourceManager.getMesh(resName)
                self.objectManager.addMesh(mesh, pos=pos)
            elif cmd == COMMAND.REQUEST_RESOURCE_LIST:
                resourceList = self.resourceManager.getResourceList()
                self.uiCmdQueue.put(COMMAND.TRANS_RESOURCE_LIST, resourceList)
            elif cmd == COMMAND.REQUEST_RESOURCE_ATTRIBUTE:
                resName, resType = value
                attribute = self.resourceManager.getResourceAttribute(resName, resType)
                if attribute:
                    self.uiCmdQueue.put(COMMAND.TRANS_RESOURCE_ATTRIBUTE, attribute)
            elif cmd == COMMAND.REQUEST_OBJECT_ATTRIBUTE:
                attribute = self.objectManager.getObjectAttribute(value)
                if attribute:
                    self.uiCmdQueue.put(COMMAND.TRANS_OBJECT_ATTRIBUTE, attribute)
            # Object Message
            elif cmd == COMMAND.SET_OBJECT_ATTRIBUTE:
                objectName, attributeName, attributeValue = value
                self.objectManager.setObjectAttribute(objectName, attributeName, attributeValue)
            elif cmd == COMMAND.SET_OBJECT_SELECT:
                self.objectManager.setSelectedObject(value)
            elif cmd == COMMAND.SET_OBJECT_FOCUS:
                self.objectManager.setObjectFocus(value)

    def updateEvent(self):
        """
        process keyboard and mouse events
        :return None:
        """
        # set pos
        self.mouseDelta[:] = self.mousePos - self.mouseOldPos
        self.mouseOldPos[:] = self.mousePos
        self.wheelUp, self.wheelDown = False, False

        # Keyboard & Mouse Events
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
                        pos = [np.random.uniform(-10, 10) for i in range(3)]
                        meshName = np.random.choice(self.resourceManager.getMeshNameList())
                        mesh = self.resourceManager.getMesh(meshName)
                        self.objectManager.addMesh(mesh, pos=pos)
                elif keyDown == K_HOME:
                    obj = self.objectManager.staticMeshes[0]
                    self.objectManager.setObjectFocus(obj)
                elif keyDown == K_DELETE:
                    self.objectManager.clearObjects()
            elif eventType == MOUSEMOTION:
                self.mousePos[:] = pygame.mouse.get_pos()
            elif eventType == MOUSEBUTTONDOWN:
                self.wheelUp = event.button == 4
                self.wheelDown = event.button == 5

    def updateCamera(self):
        # get pressed key and mouse buttons
        keydown = pygame.key.get_pressed()
        btnL, btnM, btnR = pygame.mouse.get_pressed()

        # get camera
        self.camera = self.objectManager.getMainCamera()
        moveSpeed = self.delta * 10.0

        # camera move pan
        if btnL and btnR or btnM:
            self.camera.moveToRight(-self.mouseDelta[0] * 0.01)
            self.camera.moveToUp(self.mouseDelta[1] * 0.01)
        # camera rotation
        elif btnL or btnR:
            self.camera.rotationPitch(self.mouseDelta[1] * 0.03)
            self.camera.rotationYaw(self.mouseDelta[0] * 0.03)

        # camera move front/back
        if self.wheelUp:
            self.camera.moveToFront(5.0)
        elif self.wheelDown:
            self.camera.moveToFront(-5.0)

        # update camera transform
        if keydown[K_w]:
            self.camera.moveToFront(moveSpeed)
        elif keydown[K_s]:
            self.camera.moveToFront(-moveSpeed)

        if keydown[K_a]:
            self.camera.moveToRight(-moveSpeed)
        elif keydown[K_d]:
            self.camera.moveToRight(moveSpeed)

        if keydown[K_q]:
            self.camera.moveToUp(moveSpeed)
        elif keydown[K_e]:
            self.camera.moveToUp(-moveSpeed)

        if keydown[K_SPACE]:
            self.camera.resetTransform()

        # update camera matrix to inverse matrix
        self.camera.updateInverseTransform()

    def update(self):        
        self.currentTime = 0.0
        self.running = True
        while self.running:
            currentTime = time.perf_counter()
            delta = currentTime - self.currentTime
            
            if delta < self.minDelta:
                continue

            # set timer
            self.currentTime = currentTime
            self.delta = delta
            self.fps = 1.0 / delta

            self.updateTime = delta * 1000.0  # millisecond

            # update logic
            startTime = time.perf_counter()
            self.updateCommand()  # update command queue
            self.updateEvent()  # update keyboard and mouse events
            self.updateCamera()  # update camera
            self.logicTime = (time.perf_counter() - startTime) * 1000.0  # millisecond

            # render scene
            startTime = time.perf_counter()
            self.renderer.renderScene()
            self.renderTime = (time.perf_counter() - startTime) * 1000.0  # millisecond

            # debug info
            print(self.fps, self.updateTime)
            self.console.info("%.2f fps" % self.fps)
            self.console.info("%.2f ms" % self.updateTime)
            self.console.info("CPU : %.2f ms" % self.logicTime)
            self.console.info("GPU : %.2f ms" % self.renderTime)
            
            # selected object transform info
            selectedObject = self.objectManager.getSelectedObject()
            if selectedObject:
                self.console.info("Selected Object : %s" % selectedObject.name)
                self.console.info(selectedObject.getTransformInfos())
