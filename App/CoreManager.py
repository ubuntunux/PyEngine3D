import importlib
import gc
import os
import platform as platformModule
import sys
import time
import re
import traceback
from functools import partial

import numpy as np

from .GameBackend import PyGlet, PyGame, Keyboard, Event
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
        self.valid = True

        # command
        self.cmdQueue = None
        self.uiCmdQueue = None
        self.cmdPipe = None

        self.need_to_gc_collect = False

        self.is_play_mode = False

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

        self.min_delta = sys.float_info.max
        self.max_delta = sys.float_info.min
        self.curr_min_delta = sys.float_info.max
        self.curr_max_delta = sys.float_info.min
        self.avg_fps = 0.0
        self.avg_ms = 0.0
        self.frame_count = 0
        self.acc_time = 0.0

        self.avg_logicTime = 0.0
        self.avg_gpuTime = 0.0
        self.avg_renderTime = 0.0
        self.avg_presentTime = 0.0

        self.acc_logicTime = 0.0
        self.acc_gpuTime = 0.0
        self.acc_renderTime = 0.0
        self.acc_presentTime = 0.0

        # managers
        self.script_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.render_option_manager = None
        self.renderer = None
        self.rendertarget_manager = None
        self.font_manager = None
        self.scene_manager = None
        self.particle_manager = None
        self.project_manager = None
        self.config = None

        self.last_game_backend = PyGlet.__name__
        self.game_backend_list = [PyGlet.__name__, PyGame.__name__]

        self.commands = []

    def gc_collect(self):
        self.need_to_gc_collect = True

    def initialize(self, cmdQueue, uiCmdQueue, cmdPipe, project_filename=""):
        # process start
        logger.info('Platform : %s' % platformModule.platform())
        logger.info("Process Start : %s" % GetClassName(self))

        self.cmdQueue = cmdQueue
        self.uiCmdQueue = uiCmdQueue
        self.cmdPipe = cmdPipe

        self.config = Config("config.ini", log_level)

        self.regist_command()

        # ready to launch - send message to ui
        if self.cmdPipe:
            self.cmdPipe.SendAndRecv(COMMAND.UI_RUN, None, COMMAND.UI_RUN_OK, None)

        from ResourceManager import ResourceManager
        from Object import RenderTargetManager, FontManager, RenderOptionManager, ParticleManager
        from .Renderer import Renderer
        from .SceneManager import SceneManager
        from .ProjectManager import ProjectManager

        self.resource_manager = ResourceManager.instance()
        self.render_option_manager = RenderOptionManager.instance()
        self.rendertarget_manager = RenderTargetManager.instance()
        self.font_manager = FontManager.instance()
        self.renderer = Renderer.instance()
        self.scene_manager = SceneManager.instance()
        self.particle_manager = ParticleManager.instance()
        self.project_manager = ProjectManager.instance()

        # check invalid project
        if not self.project_manager.initialize(self, project_filename):
            self.valid = False
            self.exit()
            return False

        # display_gl_info
        self.renderer.display_gl_info()

        # do First than other manager initalize. Because have to been opengl init from pygame.display.set_mode
        width, height = self.project_manager.config.Screen.size
        full_screen = self.project_manager.config.Screen.full_screen

        if self.config.hasValue('Project', 'game_backend'):
            self.last_game_backend = self.config.getValue('Project', 'game_backend')

        if self.last_game_backend == PyGame.__name__:
            self.game_backend = PyGame(self)
        else:
            self.game_backend = PyGlet(self)
            self.last_game_backend = PyGlet.__name__
        self.game_backend.change_resolution(width, height, full_screen, resize_scene=False)

        self.send_game_backend_list(self.game_backend_list)
        index = self.game_backend_list.index(
            self.last_game_backend) if self.last_game_backend in self.game_backend_list else 0
        self.send_current_game_backend_index(index)

        if not self.game_backend.valid:
            self.error('game_backend initializing failed')

        # initalize managers
        self.resource_manager.initialize(self, self.project_manager.project_dir)
        self.render_option_manager.initialize(self)
        self.rendertarget_manager.initialize(self)
        self.font_manager.initialize(self)
        self.renderer.initialize(self)
        self.renderer.resizeScene(width, height)
        self.scene_manager.initialize(self)

        main_script = self.script_manager = self.resource_manager.get_script('main')
        self.script_manager = main_script.ScriptManager.instance()
        self.script_manager.initialize(self)

        self.send(COMMAND.SORT_UI_ITEMS)
        return True

    def set_window_title(self, title):
        self.game_backend.set_window_title(self.last_game_backend + " - " + title)

    def get_next_open_project_filename(self):
        return self.project_manager.next_open_project_filename

    def run(self):
        self.game_backend.run()
        self.exit()

    def exit(self):
        # send a message to close ui
        if self.uiCmdQueue:
            self.uiCmdQueue.put(COMMAND.CLOSE_UI)

        # write config
        if self.valid:
            self.config.setValue("Project", "recent", self.project_manager.project_filename)
            self.config.setValue("Project", "game_backend", self.last_game_backend)
            self.config.save()  # save config

        # save project
        self.project_manager.close_project()

        self.renderer.close()
        self.resource_manager.close()
        self.renderer.destroyScreen()

        self.game_backend.quit()

        logger.info("Process Stop : %s" % GetClassName(self))  # process stop

    def error(self, msg):
        logger.error(msg)
        self.close()

    def close(self):
        self.game_backend.close()

    def change_game_backend(self, game_backend):
        self.last_game_backend = self.game_backend_list[game_backend]
        logger.info("The game backend was chaned to %s. It will be applied at the next run." % self.last_game_backend)

    # Send messages
    def send(self, *args):
        """
        :param args: command, value1, value2,...
        """
        if self.uiCmdQueue:
            self.uiCmdQueue.put(*args)

    def request(self, *args):
        """
        :param args: command, value1, value2,...
        """
        if self.cmdQueue:
            self.cmdQueue.put(*args)

    def send_object_attribute(self, attribute):
        self.send(COMMAND.TRANS_OBJECT_ATTRIBUTE, attribute)

    def send_resource_info(self, resource_info):
        self.send(COMMAND.TRANS_RESOURCE_INFO, resource_info)

    def notify_delete_resource(self, resource_info):
        self.send(COMMAND.DELETE_RESOURCE_INFO, resource_info)

    def send_object_info(self, obj):
        object_name = obj.name if hasattr(obj, 'name') else str(obj)
        object_class_name = GetClassName(obj)
        self.send(COMMAND.TRANS_OBJECT_INFO, (object_name, object_class_name))

    def send_object_list(self):
        obj_names = self.scene_manager.get_object_names()
        for obj_name in obj_names:
            obj = self.scene_manager.get_object(obj_name)
            self.send_object_info(obj)

    def notify_change_resolution(self, screen_info):
        self.send(COMMAND.TRANS_SCREEN_INFO, screen_info)

    def notify_clear_scene(self):
        self.send(COMMAND.CLEAR_OBJECT_LIST)

    def notify_delete_object(self, obj_name):
        self.send(COMMAND.DELETE_OBJECT_INFO, obj_name)

    def clear_render_target_list(self):
        self.send(COMMAND.CLEAR_RENDERTARGET_LIST)

    def send_render_target_info(self, rendertarget_info):
        self.send(COMMAND.TRANS_RENDERTARGET_INFO, rendertarget_info)

    def send_anti_aliasing_list(self, antialiasing_list):
        self.send(COMMAND.TRANS_ANTIALIASING_LIST, antialiasing_list)

    def send_rendering_type_list(self, rendering_type_list):
        self.send(COMMAND.TRANS_RENDERING_TYPE_LIST, rendering_type_list)

    def send_current_game_backend_index(self, game_backend_index):
        self.send(COMMAND.TRANS_GAME_BACKEND_INDEX, game_backend_index)

    def send_game_backend_list(self, game_backend_list):
        self.send(COMMAND.TRANS_GAME_BACKEND_LIST, game_backend_list)

    def regist_command(self):
        def nothing(cmd_enum, value):
            logger.warn("Nothing to do for %s(%d)" % (str(cmd_enum), cmd_enum.value))

        self.commands = []
        for i in range(COMMAND.COUNT.value):
            self.commands.append(partial(nothing, COMMAND.convert_index_to_enum(i)))

        # exit
        self.commands[COMMAND.CLOSE_APP.value] = lambda value: self.close()

        # play mode
        def cmd_play(value):
            self.is_play_mode = True
            self.resource_manager.script_loader.reload()
            main_script = self.resource_manager.get_script('main')
            self.script_manager = main_script.ScriptManager.instance()
            self.script_manager.initialize(self)
        self.commands[COMMAND.PLAY.value] = cmd_play

        def cmd_stop(value):
            self.is_play_mode = False
            self.script_manager.exit()
        self.commands[COMMAND.STOP.value] = cmd_stop

        # project
        self.commands[COMMAND.NEW_PROJECT.value] = lambda value: self.project_manager.new_project(value)
        self.commands[COMMAND.OPEN_PROJECT.value] = lambda value: self.project_manager.open_project_next_time(value)
        self.commands[COMMAND.SAVE_PROJECT.value] = lambda value: self.project_manager.save_project()
        # scene
        self.commands[COMMAND.NEW_SCENE.value] = lambda value: self.scene_manager.new_scene()
        self.commands[COMMAND.SAVE_SCENE.value] = lambda value: self.scene_manager.save_scene()
        # view mode
        self.commands[COMMAND.VIEWMODE_WIREFRAME.value] = lambda value: self.renderer.set_view_mode(
            COMMAND.VIEWMODE_WIREFRAME)
        self.commands[COMMAND.VIEWMODE_SHADING.value] = lambda value: self.renderer.set_view_mode(
            COMMAND.VIEWMODE_SHADING)

        # screen
        def cmd_change_resolution(value):
            width, height, full_screen = value
            self.game_backend.change_resolution(width, height, full_screen)
        self.commands[COMMAND.CHANGE_RESOLUTION.value] = cmd_change_resolution

        # Resource commands
        def cmd_load_resource(value):
            resName, resTypeName = value
            self.resource_manager.load_resource(resName, resTypeName)
        self.commands[COMMAND.LOAD_RESOURCE.value] = cmd_load_resource

        def cmd_action_resource(value):
            resName, resTypeName = value
            self.resource_manager.action_resource(resName, resTypeName)
        self.commands[COMMAND.ACTION_RESOURCE.value] = cmd_action_resource

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
            resourceList = self.resource_manager.get_resource_name_and_type_list()
            self.send(COMMAND.TRANS_RESOURCE_LIST, resourceList)
        self.commands[COMMAND.REQUEST_RESOURCE_LIST.value] = cmd_request_resource_list

        def cmd_request_resource_attribute(value):
            resName, resTypeName = value
            attribute = self.resource_manager.get_resource_attribute(resName, resTypeName)
            if attribute:
                self.send(COMMAND.TRANS_RESOURCE_ATTRIBUTE, attribute)
        self.commands[COMMAND.REQUEST_RESOURCE_ATTRIBUTE.value] = cmd_request_resource_attribute

        def cmd_set_resource_attribute(value):
            resource_name, resource_type, attribute_name, attribute_value, parent_info, attribute_index = value
            self.resource_manager.set_resource_attribute(resource_name,
                                                         resource_type,
                                                         attribute_name,
                                                         attribute_value,
                                                         parent_info,
                                                         attribute_index)
        self.commands[COMMAND.SET_RESOURCE_ATTRIBUTE.value] = cmd_set_resource_attribute

        def cmd_add_resource_component(value):
            resource_name, resource_type, attribute_name, parent_info, attribute_index = value
            self.resource_manager.add_resource_component(resource_name,
                                                         resource_type,
                                                         attribute_name,
                                                         parent_info,
                                                         attribute_index)
        self.commands[COMMAND.ADD_RESOURCE_COMPONENT.value] = cmd_add_resource_component

        def cmd_delete_resource_component(value):
            resource_name, resource_type, attribute_name, parent_info, attribute_index = value
            self.resource_manager.delete_resource_component(resource_name,
                                                            resource_type,
                                                            attribute_name,
                                                            parent_info,
                                                            attribute_index)
        self.commands[COMMAND.DELETE_RESOURCE_COMPONENT.value] = cmd_delete_resource_component

        # add to scene
        self.commands[COMMAND.ADD_CAMERA.value] = lambda value: self.scene_manager.add_camera()
        self.commands[COMMAND.ADD_LIGHT.value] = lambda value: self.scene_manager.add_light()

        # create resource
        self.commands[COMMAND.CREATE_PARTICLE.value] = lambda value: self.resource_manager.particle_loader.create_particle()

        self.commands[COMMAND.REQUEST_OBJECT_LIST.value] = lambda value: self.send_object_list()
        self.commands[COMMAND.ACTION_OBJECT.value] = lambda value: self.scene_manager.action_object(value)
        self.commands[COMMAND.DELETE_OBJECT.value] = lambda value: self.scene_manager.delete_object(value)

        def cmd_request_object_attribute(value):
            objName, objTypeName = value
            attribute = self.scene_manager.get_object_attribute(objName, objTypeName)
            if attribute:
                self.send(COMMAND.TRANS_OBJECT_ATTRIBUTE, attribute)
        self.commands[COMMAND.REQUEST_OBJECT_ATTRIBUTE.value] = cmd_request_object_attribute

        def cmd_set_object_attribute(value):
            objectName, objectType, attribute_name, attribute_value, parent_info, attribute_index = value
            self.scene_manager.set_object_attribute(objectName, objectType, attribute_name, attribute_value,
                                                    parent_info, attribute_index)
        self.commands[COMMAND.SET_OBJECT_ATTRIBUTE.value] = cmd_set_object_attribute

        self.commands[COMMAND.SET_OBJECT_SELECT.value] = lambda value: self.scene_manager.set_selected_object(value)
        self.commands[COMMAND.SET_OBJECT_FOCUS.value] = lambda value: self.scene_manager.set_object_focus(value)

        def cmd_set_anti_aliasing(anti_aliasing_index):
            self.renderer.postprocess.set_anti_aliasing(anti_aliasing_index)
        self.commands[COMMAND.SET_ANTIALIASING.value] = cmd_set_anti_aliasing

        def cmd_set_rendering_type(renderering_type):
            self.render_option_manager.set_rendering_type(renderering_type)
        self.commands[COMMAND.SET_RENDERING_TYPE.value] = cmd_set_rendering_type

        # set game backend
        self.commands[COMMAND.CHANGE_GAME_BACKEND.value] = self.change_game_backend

        def cmd_recreate_render_targets(value):
            self.renderer.framebuffer_manager.clear_framebuffer()
            self.renderer.rendertarget_manager.create_rendertargets()
            self.scene_manager.reset_light_probe()
            self.scene_manager.atmosphere.initialize()
        self.commands[COMMAND.RECREATE_RENDER_TARGETS.value] = cmd_recreate_render_targets

        def cmd_view_rendertarget(value):
            rendertarget_index, rendertarget_name = value
            texture = self.rendertarget_manager.find_rendertarget(rendertarget_index, rendertarget_name)
            self.renderer.set_debug_texture(texture)
            if self.renderer.debug_texture:
                attribute = self.renderer.debug_texture.get_attribute()
                self.send(COMMAND.TRANS_OBJECT_ATTRIBUTE, attribute)
        self.commands[COMMAND.VIEW_RENDERTARGET.value] = cmd_view_rendertarget

        def cmd_view_texture(value):
            texture = self.resource_manager.get_texture(value)
            self.renderer.set_debug_texture(texture)
            if texture is not None:
                attribute = texture.get_attribute()
                self.send(COMMAND.TRANS_OBJECT_ATTRIBUTE, attribute)
        self.commands[COMMAND.VIEW_TEXTURE.value] = cmd_view_texture

        def cmd_view_material_instance(value):
            material_instance = self.resource_manager.get_material_instance(value)
            if material_instance is not None and value == material_instance.name:
                self.renderer.postprocess.set_render_material_instance(material_instance)
                attribute = material_instance.get_attribute()
                self.send(COMMAND.TRANS_OBJECT_ATTRIBUTE, attribute)
        self.commands[COMMAND.VIEW_MATERIAL_INSTANCE.value] = cmd_view_material_instance

    def updateCommand(self):
        if self.uiCmdQueue is None:
            return

        while not self.cmdQueue.empty():
            # receive value must be tuple type
            cmd, value = self.cmdQueue.get()
            self.commands[cmd.value](value)

    def get_mouse_pos(self):
        return self.game_backend.mouse_pos

    def update_event(self, event_type, event_value=None):
        if Event.QUIT == event_type:
            self.close()
        elif Event.VIDEORESIZE == event_type:
            self.notify_change_resolution(event_value)
        elif Event.KEYDOWN == event_type:
            key_pressed = self.game_backend.get_keyboard_pressed()
            subkey_down = key_pressed[Keyboard.LCTRL] or key_pressed[Keyboard.LSHIFT] or key_pressed[Keyboard.LALT]
            if Keyboard.ESCAPE == event_value:
                if self.game_backend.full_screen:
                    self.game_backend.change_resolution(0, 0, False)
                else:
                    self.close()
            elif Keyboard._1 == event_value:
                models = self.resource_manager.model_loader.get_resource_list()
                if models:
                    for i in range(20):
                        pos = [np.random.uniform(-10, 10) for x in range(3)]
                        model = np.random.choice(models)
                        obj_instance = self.scene_manager.add_object(model=model.get_data(), pos=pos)
                        if obj_instance:
                            self.send_object_info(obj_instance)
            elif Keyboard._2 == event_value:
                self.scene_manager.reset_light_probe()
            elif Keyboard._3 == event_value:
                self.gc_collect()
            elif Keyboard.DELETE == event_value:
                # Test Code
                obj_names = set(self.scene_manager.get_object_names())
                # clear static mesh
                self.scene_manager.clear_actors()
                current_obj_names = set(self.scene_manager.get_object_names())
                for obj_name in (obj_names - current_obj_names):
                    self.notify_delete_object(obj_name)

    def update_camera(self):
        keydown = self.game_backend.get_keyboard_pressed()
        mouse_delta = self.game_backend.mouse_delta
        btnL, btnM, btnR = self.game_backend.get_mouse_pressed()

        # get camera
        camera = self.scene_manager.main_camera
        cameraTransform = camera.transform
        move_speed = camera.move_speed * self.delta
        pan_speed = camera.pan_speed * self.delta
        rotation_speed = camera.rotation_speed * self.delta

        if keydown[Keyboard.LSHIFT]:
            move_speed *= 4.0
            pan_speed *= 4.0

        # camera move pan
        if btnL and btnR or btnM:
            cameraTransform.move_to_left(-mouse_delta[0] * pan_speed)
            cameraTransform.move_to_up(-mouse_delta[1] * pan_speed)

        # camera rotation
        elif btnL or btnR:
            cameraTransform.rotation_pitch(mouse_delta[1] * rotation_speed)
            cameraTransform.rotation_yaw(-mouse_delta[0] * rotation_speed)

        if keydown[Keyboard.Z]:
            cameraTransform.rotation_roll(-rotation_speed * 10.0)
        elif keydown[Keyboard.C]:
            cameraTransform.rotation_roll(rotation_speed * 10.0)

        # move to view direction ( inverse front of camera matrix )
        if keydown[Keyboard.W] or self.game_backend.wheel_up:
            cameraTransform.move_to_front(-move_speed)
        elif keydown[Keyboard.S] or self.game_backend.wheel_down:
            cameraTransform.move_to_front(move_speed)

        # move to side
        if keydown[Keyboard.A]:
            cameraTransform.move_to_left(-move_speed)
        elif keydown[Keyboard.D]:
            cameraTransform.move_to_left(move_speed)

        # move to up
        if keydown[Keyboard.Q]:
            cameraTransform.move_to_up(move_speed)
        elif keydown[Keyboard.E]:
            cameraTransform.move_to_up(-move_speed)

        if keydown[Keyboard.SPACE]:
            cameraTransform.reset_transform()

    def update(self):
        currentTime = time.perf_counter()
        delta = currentTime - self.currentTime

        if self.vsync and delta < self.minDelta or delta == 0.0:
            return

        self.acc_time += delta
        self.frame_count += 1
        self.curr_min_delta = min(delta, self.curr_min_delta)
        self.curr_max_delta = max(delta, self.curr_max_delta)

        # set timer
        self.currentTime = currentTime
        self.delta = delta
        self.fps = 1.0 / delta

        self.updateTime = delta * 1000.0  # millisecond

        startTime = time.perf_counter()
        self.updateCommand()

        if self.is_play_mode:
            self.script_manager.update(delta)
        else:
            self.update_camera()

        # update actors
        self.scene_manager.update_scene(delta)
        self.logicTime = (time.perf_counter() - startTime) * 1000.0  # millisecond

        # render scene
        startTime = time.perf_counter()
        self.renderer.render_light_probe(self.scene_manager.main_light_probe)
        renderTime, presentTime = self.renderer.renderScene()

        self.renderTime = renderTime * 1000.0  # millisecond
        self.presentTime = presentTime * 1000.0  # millisecond

        self.acc_logicTime += self.logicTime
        self.acc_gpuTime += self.gpuTime
        self.acc_renderTime += self.renderTime
        self.acc_presentTime += self.presentTime

        if 1.0 < self.acc_time:
            self.avg_logicTime = self.acc_logicTime / self.frame_count
            self.avg_gpuTime = self.acc_gpuTime / self.frame_count
            self.avg_renderTime = self.acc_renderTime / self.frame_count
            self.avg_presentTime = self.acc_presentTime / self.frame_count

            self.acc_logicTime = 0.0
            self.acc_gpuTime = 0.0
            self.acc_renderTime = 0.0
            self.acc_presentTime = 0.0

            self.min_delta = self.curr_min_delta * 1000.0
            self.max_delta = self.curr_max_delta * 1000.0
            self.curr_min_delta = sys.float_info.max
            self.curr_max_delta = sys.float_info.min
            self.avg_ms = self.acc_time / self.frame_count * 1000.0
            self.avg_fps = 1000.0 / self.avg_ms
            self.frame_count = 0
            self.acc_time = 0.0

        # debug info
        # print(self.fps, self.updateTime)
        self.font_manager.log("%.2f fps" % self.avg_fps)
        self.font_manager.log("%.2f ms (%.2f ms ~ %.2f ms)" % (self.avg_ms, self.min_delta, self.max_delta))
        self.font_manager.log("CPU : %.2f ms" % self.avg_logicTime)
        self.font_manager.log("GPU : %.2f ms" % self.avg_gpuTime)
        self.font_manager.log("Render : %.2f ms" % self.avg_renderTime)
        self.font_manager.log("Present : %.2f ms" % self.avg_presentTime)

        render_count = len(self.scene_manager.skeleton_solid_render_infos)
        render_count += len(self.scene_manager.skeleton_translucent_render_infos)
        render_count += len(self.scene_manager.static_solid_render_infos)
        render_count += len(self.scene_manager.static_translucent_render_infos)
        self.font_manager.log("Render Count : %d" % render_count)
        self.font_manager.log("Point Lights : %d" % self.scene_manager.point_light_count)
        self.font_manager.log("Particle Count : %d" % len(self.particle_manager.render_particles))

        # selected object transform info
        selected_object = self.scene_manager.get_selected_object()
        if selected_object:
            self.font_manager.log("Selected Object : %s" % selected_object.name)
            if hasattr(selected_object, 'transform'):
                self.font_manager.log(selected_object.transform.get_transform_infos())
        self.gpuTime = (time.perf_counter() - startTime) * 1000.0

        if self.need_to_gc_collect:
            self.need_to_gc_collect = False
            gc.collect()

