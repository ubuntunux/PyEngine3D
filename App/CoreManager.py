import os
import platform as platformModule
import sys
import time
import re
import traceback
from functools import partial

import numpy as np
import pygame
from pygame.locals import *

from Common import logger, log_level, COMMAND
from Utilities import Singleton, GetClassName, Config, Profiler

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
        self.vsync = False
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
        self.font_manager = None
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
        from Object import RenderTargetManager, Renderer, FontManager
        from .SceneManager import SceneManager
        from .ProjectManager import ProjectManager

        self.resource_manager = ResourceManager.instance()
        self.rendertarget_manager = RenderTargetManager.instance()
        self.font_manager = FontManager.instance()
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
        full_screen = self.projectManager.config.Screen.full_screen
        Renderer.change_resolution(width, height, full_screen)

        # initalize managers
        self.resource_manager.initialize(self, self.projectManager.project_dir)
        self.rendertarget_manager.initialize(self)
        self.font_manager.initialize(self)
        self.renderer.initialize(self)
        self.sceneManager.initialize(self)

        # build a scene - windows not need resize..
        if not self.renderer.created_scene:
            if platformModule.system() == 'Linux':
                self.renderer.resizeScene(width, height, full_screen)

        self.send(COMMAND.SORT_UI_ITEMS)
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

    def request(self, *args):
        if self.cmdQueue:
            self.cmdQueue.put(*args)

    def sendResourceInfo(self, resource_info):
        self.send(COMMAND.TRANS_RESOURCE_INFO, resource_info)

    def notifyDeleteResource(self, resource_info):
        self.send(COMMAND.DELETE_RESOURCE_INFO, resource_info)

    def sendObjectInfo(self, obj):
        object_name = obj.name if hasattr(obj, 'name') else str(obj)
        object_class_name = GetClassName(obj)
        self.send(COMMAND.TRANS_OBJECT_INFO, (object_name, object_class_name))

    def sendObjectList(self):
        obj_names = self.sceneManager.getObjectNames()
        for obj_name in obj_names:
            obj = self.sceneManager.getObject(obj_name)
            self.sendObjectInfo(obj)

    def notifyChangeResolution(self, screen_info):
        self.send(COMMAND.TRANS_SCREEN_INFO, screen_info)

    def notifyClearScene(self):
        self.send(COMMAND.CLEAR_OBJECT_LIST)

    def notifyDeleteObject(self, obj_name):
        self.send(COMMAND.DELETE_OBJECT_INFO, obj_name)

    def clearRenderTargetList(self):
        self.send(COMMAND.CLEAR_RENDERTARGET_LIST)

    def sendRenderTargetInfo(self, rendertarget_info):
        self.send(COMMAND.TRANS_RENDERTARGET_INFO, rendertarget_info)

    def sendAntiAliasingList(self, antialiasing_list):
        self.send(COMMAND.TRANS_ANTIALIASING_LIST, antialiasing_list)

    def sendRenderingTypeList(self, rendering_type_list):
        self.send(COMMAND.TRANS_RENDERING_TYPE_LIST, rendering_type_list)

    def registCommand(self):
        def nothing(cmd_enum, value):
            logger.warn("Nothing to do for %s(%d)" % (str(cmd_enum), cmd_enum.value))

        self.commands = []
        for i in range(COMMAND.COUNT.value):
            self.commands.append(partial(nothing, COMMAND.convert_index_to_enum(i)))

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

        # screen
        def cmd_change_resolution(value):
            width, height, full_screen = value
            self.renderer.resizeScene(width, height, full_screen)
        self.commands[COMMAND.CHANGE_RESOLUTION.value] = cmd_change_resolution

        # Resource commands
        def cmd_load_resource(value):
            resName, resTypeName = value
            self.resource_manager.load_resource(resName, resTypeName)
        self.commands[COMMAND.LOAD_RESOURCE.value] = cmd_load_resource

        def cmd_open_resource(value):
            resName, resTypeName = value
            self.resource_manager.open_resource(resName, resTypeName)
        self.commands[COMMAND.OPEN_RESOURCE.value] = cmd_open_resource

        def cmd_duplicate_resource(value):
            resName, resTypeName = value
            self.resource_manager.duplicate_resource(resName, resTypeName)
        self.commands[COMMAND.DUPLICATE_RESOURCE.value] = cmd_duplicate_resource

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
            objName, objTypeName = value
            attribute = self.sceneManager.getObjectAttribute(objName, objTypeName)
            if attribute:
                self.send(COMMAND.TRANS_OBJECT_ATTRIBUTE, attribute)
        self.commands[COMMAND.REQUEST_OBJECT_ATTRIBUTE.value] = cmd_request_object_attribute

        def cmd_set_object_attribute(value):
            objectName, objectType, attributeName, attributeValue, attribute_index = value
            self.sceneManager.setObjectAttribute(objectName, objectType, attributeName, attributeValue, attribute_index)
        self.commands[COMMAND.SET_OBJECT_ATTRIBUTE.value] = cmd_set_object_attribute

        self.commands[COMMAND.SET_OBJECT_SELECT.value] = lambda value: self.sceneManager.setSelectedObject(value)
        self.commands[COMMAND.SET_OBJECT_FOCUS.value] = lambda value: self.sceneManager.setObjectFocus(value)

        def cmd_set_anti_aliasing(anti_aliasing_index):
            self.renderer.postprocess.set_anti_aliasing(anti_aliasing_index)
        self.commands[COMMAND.SET_ANTIALIASING.value] = cmd_set_anti_aliasing

        def cmd_set_rendering_type(renderering_type):
            self.renderer.set_rendering_type(renderering_type)
        self.commands[COMMAND.SET_RENDERING_TYPE.value] = cmd_set_rendering_type

        def cmd_view_rendertarget(value):
            rendertarget_index, rendertarget_name = value
            self.renderer.set_debug_rendertarget(rendertarget_index, rendertarget_name)
            if self.renderer.debug_rendertarget:
                attribute = self.renderer.debug_rendertarget.getAttribute()
                if attribute:
                    self.send(COMMAND.TRANS_OBJECT_ATTRIBUTE, attribute)
        self.commands[COMMAND.VIEW_RENDERTARGET.value] = cmd_view_rendertarget

        def cmd_recreate_render_targets(value):
            self.renderer.rendertarget_manager.create_rendertargets()
        self.commands[COMMAND.RECREATE_RENDER_TARGETS.value] = cmd_recreate_render_targets

    def updateCommand(self):
        if self.uiCmdQueue is None:
            return

        while not self.cmdQueue.empty():
            # receive value must be tuple type
            cmd, value = self.cmdQueue.get()
            self.commands[cmd.value](value)

    def event_object(self, keyDown, key_pressed):
        done = False
        if keyDown == K_1:
            object_name_list = self.resource_manager.getModelNameList()
            if object_name_list:
                for i in range(20):
                    pos = [np.random.uniform(-100, 100) for x in range(3)]
                    objName = np.random.choice(object_name_list)
                    model = self.resource_manager.getModel(objName)
                    obj_instance = self.sceneManager.addObject(model=model, pos=pos)
                    if obj_instance:
                        self.sendObjectInfo(obj_instance)
            done = True
        elif keyDown == K_DELETE:
            # Test Code
            obj_names = set(self.sceneManager.getObjectNames())
            # clear static mesh
            self.sceneManager.clear_actors()
            current_obj_names = set(self.sceneManager.getObjectNames())
            for obj_name in (obj_names - current_obj_names):
                self.notifyDeleteObject(obj_name)
            done = True
        return done

    def updateEvent(self):
        self.mouseDelta[...] = self.mousePos - self.mouseOldPos
        self.mouseOldPos[...] = self.mousePos
        self.wheelUp, self.wheelDown = False, False
        key_pressed = pygame.key.get_pressed()

        # Keyboard & Mouse Events
        for event in pygame.event.get():
            eventType = event.type
            if eventType == QUIT:
                self.close()
            elif eventType == VIDEORESIZE:
                pass
                # self.renderer.resizeScene(*event.dict['size'], self.renderer.full_screen)
            elif eventType == KEYDOWN:
                subkey_down = key_pressed[K_LCTRL] or key_pressed[K_LSHIFT] or key_pressed[K_LALT]
                keyDown = event.key
                if self.event_object(keyDown, key_pressed):
                    pass
                elif keyDown == K_ESCAPE:
                    if self.renderer.full_screen:
                        self.renderer.resizeScene(0, 0, not self.renderer.full_screen)
                    else:
                        self.close()
                elif keyDown == K_BACKQUOTE and not subkey_down:
                    pass
            elif eventType == MOUSEMOTION:
                self.mousePos[...] = pygame.mouse.get_pos()
            elif eventType == MOUSEBUTTONDOWN:
                self.wheelUp = event.button == 4
                self.wheelDown = event.button == 5

    def updateCamera(self):
        # get pressed key and mouse buttons
        keydown = pygame.key.get_pressed()
        btnL, btnM, btnR = pygame.mouse.get_pressed()

        # get camera
        camera = self.sceneManager.mainCamera
        cameraTransform = camera.transform
        move_speed = camera.move_speed * self.delta
        pan_speed = camera.pan_speed * self.delta
        rotation_speed = camera.rotation_speed * self.delta

        if keydown[K_LSHIFT]:
            move_speed *= 4.0
            pan_speed *= 4.0

        # camera move pan
        if btnL and btnR or btnM:
            cameraTransform.moveToLeft(-self.mouseDelta[0] * pan_speed)
            cameraTransform.moveToUp(self.mouseDelta[1] * pan_speed)

        # camera rotation
        elif btnL or btnR:
            cameraTransform.rotationPitch(-self.mouseDelta[1] * rotation_speed)
            cameraTransform.rotationYaw(-self.mouseDelta[0] * rotation_speed)

        if keydown[K_z]:
            cameraTransform.rotationRoll(-rotation_speed * 10.0)
        elif keydown[K_c]:
            cameraTransform.rotationRoll(rotation_speed * 10.0)

        # move to view direction ( inverse front of camera matrix )
        if keydown[K_w] or self.wheelUp:
            cameraTransform.moveToFront(-move_speed)
        elif keydown[K_s] or self.wheelDown:
            cameraTransform.moveToFront(move_speed)

        # move to side
        if keydown[K_a]:
            cameraTransform.moveToLeft(-move_speed)
        elif keydown[K_d]:
            cameraTransform.moveToLeft(move_speed)

        # move to up
        if keydown[K_q]:
            cameraTransform.moveToUp(move_speed)
        elif keydown[K_e]:
            cameraTransform.moveToUp(-move_speed)

        if keydown[K_SPACE]:
            cameraTransform.resetTransform()

    def update(self):
        self.currentTime = 0.0
        self.running = True

        min_delta = sys.float_info.max
        max_delta = sys.float_info.min
        curr_min_delta = sys.float_info.max
        curr_max_delta = sys.float_info.min
        avg_fps = 0.0
        avg_ms = 0.0
        frame_count = 0
        acc_time = 0.0

        avg_logicTime = 0.0
        avg_gpuTime = 0.0
        avg_renderTime = 0.0
        avg_presentTime = 0.0

        acc_logicTime = 0.0
        acc_gpuTime = 0.0
        acc_renderTime = 0.0
        acc_presentTime = 0.0

        while self.running:
            currentTime = time.perf_counter()
            delta = currentTime - self.currentTime

            if self.vsync and delta < self.minDelta or delta == 0.0:
                continue

            acc_time += delta
            frame_count += 1
            curr_min_delta = min(delta, curr_min_delta)
            curr_max_delta = max(delta, curr_max_delta)

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
            self.sceneManager.update_scene(delta)

            # render scene
            startTime = time.perf_counter()
            renderTime, presentTime = self.renderer.renderScene()

            self.renderTime = renderTime * 1000.0  # millisecond
            self.presentTime = presentTime * 1000.0  # millisecond

            acc_logicTime += self.logicTime
            acc_gpuTime += self.gpuTime
            acc_renderTime += self.renderTime
            acc_presentTime += self.presentTime

            if 1.0 < acc_time:
                avg_logicTime = acc_logicTime / frame_count
                avg_gpuTime = acc_gpuTime / frame_count
                avg_renderTime = acc_renderTime / frame_count
                avg_presentTime = acc_presentTime / frame_count

                acc_logicTime = 0.0
                acc_gpuTime = 0.0
                acc_renderTime = 0.0
                acc_presentTime = 0.0

                min_delta = curr_min_delta * 1000.0
                max_delta = curr_max_delta * 1000.0
                curr_min_delta = sys.float_info.max
                curr_max_delta = sys.float_info.min
                avg_ms = acc_time / frame_count * 1000.0
                avg_fps = 1000.0 / avg_ms
                frame_count = 0
                acc_time = 0.0

            # debug info
            # print(self.fps, self.updateTime)
            self.font_manager.log("%.2f fps" % avg_fps)
            self.font_manager.log("%.2f ms (%.2f ms ~ %.2f ms)" % (avg_ms, min_delta, max_delta))
            self.font_manager.log("CPU : %.2f ms" % avg_logicTime)
            self.font_manager.log("GPU : %.2f ms" % avg_gpuTime)
            self.font_manager.log("Render : %.2f ms" % avg_renderTime)
            self.font_manager.log("Present : %.2f ms" % avg_presentTime)

            # selected object transform info
            selectedObject = self.sceneManager.getSelectedObject()
            if selectedObject:
                self.font_manager.log("Selected Object : %s" % selectedObject.name)
                self.font_manager.log(selectedObject.transform.getTransformInfos())
            self.gpuTime = (time.perf_counter() - startTime) * 1000.0
