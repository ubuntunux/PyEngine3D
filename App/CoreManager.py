import os
import platform as platformModule
import sys
import time
import re
import traceback

import numpy as np
import pygame
from pygame.locals import *

from Common import logger, log_level, COMMAND
from Utilities import Singleton, GetClassName, Config

# Function : IsExtensionSupported
# NeHe Tutorial Lesson: 45 - Vertex Buffer Objects
reCheckGLExtention = re.compile("GL_(.+?)_(.+)")


# ------------------------------#
# CLASS : CoreManager
# ------------------------------#
class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """

    def __init__(self):
        self.running = False
        self.valid = True

        # command
        self.cmdQueue = None
        self.uiCmdQueue = None
        self.cmdPipe = None

        # timer
        self.fps = 0.0
        self.minDelta = 1.0 / 60.0  # 60fps
        self.delta = 0.0
        self.updateTime = 0.0
        self.logicTime = 0.0
        self.gpuTime = 0.0
        self.renderTime = 0.0
        self.presentTime = 0.0
        self.currentTime = 0.0

        # mouse
        self.mousePos = np.zeros(2)
        self.mouseOldPos = np.zeros(2)
        self.mouseDelta = np.zeros(2)
        self.wheelUp = False
        self.wheelDown = False

        # managers
        self.resource_manager = None
        self.renderer = None
        self.rendertarget_manager = None
        self.sceneManager = None
        self.projectManager = None
        self.config = None

        self.commands = []

    def initialize(self, cmdQueue, uiCmdQueue, cmdPipe, project_filename=""):
        # process start
        logger.info('Platform : %s' % platformModule.platform())
        logger.info("Process Start : %s" % GetClassName(self))

        self.cmdQueue = cmdQueue
        self.uiCmdQueue = uiCmdQueue
        self.cmdPipe = cmdPipe

        self.config = Config("config.ini", log_level)

        self.registCommand()

        # ready to launch - send message to ui
        if self.cmdPipe:
            self.cmdPipe.SendAndRecv(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)

        from ResourceManager import ResourceManager
        from OpenGLContext import RenderTargetManager
        from .SceneManager import SceneManager
        from .ProjectManager import ProjectManager
        from .Renderer import Renderer

        self.resource_manager = ResourceManager.instance()
        self.rendertarget_manager = RenderTargetManager.instance()
        self.renderer = Renderer.instance()
        self.sceneManager = SceneManager.instance()
        self.projectManager = ProjectManager.instance()

        # check innvalid project
        if not self.projectManager.initialize(self, project_filename):
            self.valid = False
            self.exit()
            return False

        # centered window
        os.environ['SDL_VIDEO_CENTERED'] = '1'

        # pygame init
        pygame.init()
        # do First than other manager initalize. Because have to been opengl init from pygame.display.set_mode
        width, height = self.projectManager.config.Screen.size
        screen = pygame.display.set_mode((width, height), OPENGL | DOUBLEBUF | RESIZABLE | HWPALETTE | HWSURFACE)
        pygame.font.init()
        if not pygame.font.get_init():
            self.error('Could not render font.')

        # initalize managers
        self.resource_manager.initialize(self, self.projectManager.project_dir)
        self.rendertarget_manager.initialize()
        self.renderer.initialize(self, width, height, screen)
        self.sceneManager.initialize(self)

        # build a scene - windows not need resize..
        if platformModule.system() == 'Linux':
            self.renderer.resizeScene()
        return True

    @staticmethod
    def set_window_title(title):
        pygame.display.set_caption(title)

    def get_next_open_project_filename(self):
        return self.projectManager.next_open_project_filename

    def run(self):
        self.update()  # main loop
        self.exit()  # exit

    def exit(self):
        # send a message to close ui
        if self.uiCmdQueue:
            self.uiCmdQueue.put(COMMAND.CLOSE_UI)

        # write config
        if self.valid:
            self.config.setValue("Project", "recent", self.projectManager.project_filename)
            self.config.save()  # save config

        # save project
        self.projectManager.close_project()

        self.renderer.close()
        self.resource_manager.close()
        self.renderer.destroyScreen()

        pygame.quit()

        logger.info("Process Stop : %s" % GetClassName(self))  # process stop

    def error(self, msg: object) -> object:
        logger.error(msg)
        self.close()

    def close(self):
        self.running = False

    # Send messages
    def send(self, *args):
        if self.uiCmdQueue:
            self.uiCmdQueue.put(*args)

    def sendResourceInfo(self, resource_info):
        self.send(COMMAND.TRANS_RESOURCE_INFO, resource_info)

    def notifyDeleteResource(self, resource_info):
        self.send(COMMAND.DELETE_RESOURCE_INFO, resource_info)

    def sendObjectInfo(self, object_name):
        object_info = self.sceneManager.getObjectInfo(object_name)
        if object_info:
            self.send(COMMAND.TRANS_OBJECT_INFO, object_info)

    def sendObjectList(self):
        obj_names = self.sceneManager.getObjectNames()
        for obj_name in obj_names:
            self.sendObjectInfo(obj_name)

    def notifyClearScene(self):
        self.send(COMMAND.CLEAR_OBJECT_LIST)

    def notifyDeleteObject(self, obj_name):
        self.send(COMMAND.DELETE_OBJECT_INFO, obj_name)

    def registCommand(self):
        def nothing(value):
            logger.warn("Nothing to do.")
            pass

        self.commands = [nothing, ] * COMMAND.COUNT.value

        # exit
        self.commands[COMMAND.CLOSE_APP.value] = lambda value: self.close()
        # project
        self.commands[COMMAND.NEW_PROJECT.value] = lambda value: self.projectManager.new_project(value)
        self.commands[COMMAND.OPEN_PROJECT.value] = lambda value: self.projectManager.open_project_next_time(value)
        self.commands[COMMAND.SAVE_PROJECT.value] = lambda value: self.projectManager.save_project()
        # scene
        self.commands[COMMAND.NEW_SCENE.value] = lambda value: self.sceneManager.new_scene()
        self.commands[COMMAND.SAVE_SCENE.value] = lambda value: self.sceneManager.save_scene()
        # view mode
        self.commands[COMMAND.VIEWMODE_WIREFRAME.value] = lambda value: self.renderer.setViewMode(
            COMMAND.VIEWMODE_WIREFRAME)
        self.commands[COMMAND.VIEWMODE_SHADING.value] = lambda value: self.renderer.setViewMode(
            COMMAND.VIEWMODE_SHADING)

        # Resource commands
        def cmd_open_resource(value):
            resName, resTypeName = value
            self.resource_manager.open_resource(resName, resTypeName)
        self.commands[COMMAND.OPEN_RESOURCE.value] = cmd_open_resource

        def cmd_load_resource(value):
            resName, resTypeName = value
            self.resource_manager.load_resource(resName, resTypeName)
        self.commands[COMMAND.LOAD_RESOURCE.value] = cmd_load_resource

        def cmd_save_resource(value):
            resName, resTypeName = value
            self.resource_manager.save_resource(resName, resTypeName)
        self.commands[COMMAND.SAVE_RESOURCE.value] = cmd_save_resource

        def cmd_delete_resource(value):
            resName, resTypeName = value
            self.resource_manager.delete_resource(resName, resTypeName)
        self.commands[COMMAND.DELETE_RESOURCE.value] = cmd_delete_resource

        def cmd_request_resource_list(value):
            resourceList = self.resource_manager.getResourceNameAndTypeList()
            self.send(COMMAND.TRANS_RESOURCE_LIST, resourceList)
        self.commands[COMMAND.REQUEST_RESOURCE_LIST.value] = cmd_request_resource_list

        def cmd_request_resource_attribute(value):
            resName, resTypeName = value
            attribute = self.resource_manager.getResourceAttribute(resName, resTypeName)
            if attribute:
                self.send(COMMAND.TRANS_RESOURCE_ATTRIBUTE, attribute)
        self.commands[COMMAND.REQUEST_RESOURCE_ATTRIBUTE.value] = cmd_request_resource_attribute

        def cmd_set_resource_attribute(value):
            resourceName, resourceType, attributeName, attributeValue, attribute_index = value
            self.resource_manager.setResourceAttribute(resourceName, resourceType, attributeName, attributeValue,
                                                      attribute_index)
        self.commands[COMMAND.SET_RESOURCE_ATTRIBUTE.value] = cmd_set_resource_attribute

        # Scene object commands
        self.commands[COMMAND.REQUEST_OBJECT_LIST.value] = lambda value: self.sendObjectList()
        self.commands[COMMAND.DELETE_OBJECT.value] = lambda value: self.sceneManager.deleteObject(value)

        def cmd_request_object_attribute(value):
            attribute = self.sceneManager.getObjectAttribute(value)
            if attribute:
                self.send(COMMAND.TRANS_OBJECT_ATTRIBUTE, attribute)
        self.commands[COMMAND.REQUEST_OBJECT_ATTRIBUTE.value] = cmd_request_object_attribute

        def cmd_set_object_attribute(value):
            objectName, objectType, attributeName, attributeValue, attribute_index = value
            self.sceneManager.setObjectAttribute(objectName, objectType, attributeName, attributeValue, attribute_index)
        self.commands[COMMAND.SET_OBJECT_ATTRIBUTE.value] = cmd_set_object_attribute

        self.commands[COMMAND.SET_OBJECT_SELECT.value] = lambda value: self.sceneManager.setSelectedObject(value)
        self.commands[COMMAND.SET_OBJECT_FOCUS.value] = lambda value: self.sceneManager.setObjectFocus(value)

    # Recieve message
    def updateCommand(self):
        if self.uiCmdQueue is None:
            return

        while not self.cmdQueue.empty():
            # receive value must be tuple type
            cmd, value = self.cmdQueue.get()
            self.commands[cmd.value](value)

    def updateEvent(self):
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
                    self.renderer.console.toggle()
                elif keyDown == K_1:
                    object_name_list = self.resource_manager.getObjectNameList()
                    if object_name_list:
                        for i in range(100):
                            pos = [np.random.uniform(-10, 10) for x in range(3)]
                            objName = np.random.choice(object_name_list)
                            source_obj = self.resource_manager.getObject(objName)
                            obj_instance = self.sceneManager.addObject(source_object=source_obj, pos=pos)
                            if obj_instance:
                                self.sendObjectInfo(obj_instance.name)
                elif keyDown == K_HOME:
                    obj = self.sceneManager.staticMeshes[0]
                    self.sceneManager.setObjectFocus(obj)
                elif keyDown == K_DELETE:
                    # Test Code
                    obj_names = set(self.sceneManager.getObjectNames())
                    # clear static mesh
                    self.sceneManager.clearStaticMeshes()
                    current_obj_names = set(self.sceneManager.getObjectNames())
                    for obj_name in (obj_names - current_obj_names):
                        self.notifyDeleteObject(obj_name)
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
        camera = self.sceneManager.getMainCamera()
        cameraTransform = camera.transform
        move_speed = camera.move_speed * self.delta
        pan_speed = camera.pan_speed * self.delta
        rotation_speed = camera.rotation_speed * self.delta

        if keydown[K_LSHIFT]:
            move_speed *= 4.0
            pan_speed *= 4.0

        # camera move pan
        if btnL and btnR or btnM:
            cameraTransform.moveToRight(-self.mouseDelta[0] * pan_speed)
            cameraTransform.moveToUp(self.mouseDelta[1] * pan_speed)
        # camera rotation
        elif btnL or btnR:
            cameraTransform.rotationPitch(self.mouseDelta[1] * rotation_speed)
            cameraTransform.rotationYaw(self.mouseDelta[0] * rotation_speed)

        if keydown[K_z]:
            cameraTransform.rotationRoll(-rotation_speed * 10.0)
        elif keydown[K_c]:
            cameraTransform.rotationRoll(rotation_speed * 10.0)

        # camera move front/back
        if self.wheelUp:
            cameraTransform.moveToFront(move_speed)
        elif self.wheelDown:
            cameraTransform.moveToFront(-move_speed)

        # update camera transform
        if keydown[K_w]:
            cameraTransform.moveToFront(move_speed)
        elif keydown[K_s]:
            cameraTransform.moveToFront(-move_speed)

        if keydown[K_a]:
            cameraTransform.moveToRight(-move_speed)
        elif keydown[K_d]:
            cameraTransform.moveToRight(move_speed)

        if keydown[K_q]:
            cameraTransform.moveToUp(-move_speed)
        elif keydown[K_e]:
            cameraTransform.moveToUp(move_speed)

        if keydown[K_SPACE]:
            cameraTransform.resetTransform()

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

            # update actors
            self.sceneManager.update()

            # render scene
            startTime = time.perf_counter()
            renderTime, presentTime = self.renderer.renderScene()

            self.renderTime = renderTime * 1000.0  # millisecond
            self.presentTime = presentTime * 1000.0  # millisecond

            # debug info
            # print(self.fps, self.updateTime)
            self.renderer.console.info("%.2f fps" % self.fps)
            self.renderer.console.info("%.2f ms" % self.updateTime)
            self.renderer.console.info("CPU : %.2f ms" % self.logicTime)
            self.renderer.console.info("GPU : %.2f ms" % self.gpuTime)
            self.renderer.console.info("Render : %.2f ms" % self.renderTime)
            self.renderer.console.info("Present : %.2f ms" % self.presentTime)

            # selected object transform info
            selectedObject = self.sceneManager.getSelectedObject()
            if selectedObject:
                self.renderer.console.info("Selected Object : %s" % selectedObject.name)
                self.renderer.console.info(selectedObject.transform.getTransformInfos())
            self.gpuTime = (time.perf_counter() - startTime) * 1000.0
