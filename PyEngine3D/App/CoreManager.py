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

from .GameBackend import GameBackNames, Keyboard, Event, InputMode
from PyEngine3D.Common import logger, log_level, COMMAND, VIDEO_RESIZE_TIME
from PyEngine3D.Utilities import Singleton, GetClassName, Config, Profiler


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

        self.is_basic_mode = False

        # timer
        self.fps = 0.0
        self.vsync = False
        self.limit_delta = 1.0 / 60.0  # 60fps
        self.delta = 0.0
        self.update_time = 0.0
        self.logic_time = 0.0
        self.gpu_time = 0.0
        self.render_time = 0.0
        self.present_time = 0.0
        self.current_time = 0.0
        self.video_resize_time = 0.0
        self.video_resized = False

        self.min_delta = sys.float_info.max
        self.max_delta = sys.float_info.min
        self.curr_min_delta = sys.float_info.max
        self.curr_max_delta = sys.float_info.min
        self.avg_fps = 0.0
        self.avg_ms = 0.0
        self.frame_count = 0
        self.acc_time = 0.0

        self.avg_logic_time = 0.0
        self.avg_gpu_time = 0.0
        self.avg_render_time = 0.0
        self.avg_present_time = 0.0

        self.acc_logic_time = 0.0
        self.acc_gpu_time = 0.0
        self.acc_render_time = 0.0
        self.acc_present_time = 0.0

        # managers
        self.opengl_context = None
        self.script_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.render_option_manager = None
        self.renderer = None
        self.render_option = None
        self.debug_line_manager = None
        self.rendertarget_manager = None
        self.font_manager = None
        self.scene_manager = None
        self.sound_manager = None
        self.viewport_manager = None
        self.effect_manager = None
        self.project_manager = None
        self.config = None

        self.last_game_backend = GameBackNames.PYGLET
        self.game_backend_list = [GameBackNames.PYGLET, GameBackNames.PYGAME]

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

        from PyEngine3D.UI import ViewportManager
        from PyEngine3D.OpenGLContext import OpenGLContext
        from PyEngine3D.ResourceManager import ResourceManager
        from PyEngine3D.Render import Renderer, Renderer_Basic, RenderTargetManager, FontManager, RenderOptionManager, EffectManager, DebugLineManager, RenderOption
        from .SceneManager import SceneManager
        from .SoundManager import SoundManager
        from .ProjectManager import ProjectManager

        self.opengl_context = OpenGLContext
        self.viewport_manager = ViewportManager.instance()
        self.render_option_manager = RenderOptionManager.instance()
        self.rendertarget_manager = RenderTargetManager.instance()
        self.resource_manager = ResourceManager.instance()
        self.font_manager = FontManager.instance()
        self.renderer = Renderer.instance()
        self.render_option = RenderOption
        self.debug_line_manager = DebugLineManager.instance()
        self.scene_manager = SceneManager.instance()
        self.sound_manager = SoundManager.instance()
        self.effect_manager = EffectManager.instance()
        self.project_manager = ProjectManager.instance()

        # check invalid project
        if not self.project_manager.initialize(self, project_filename):
            self.valid = False
            self.exit()
            return False

        # do First than other manager initalize. Because have to been opengl init from pygame.display.set_mode
        width, height = self.project_manager.config.Screen.size
        full_screen = self.project_manager.config.Screen.full_screen

        if self.config.hasValue('Project', 'game_backend'):
            self.last_game_backend = self.config.getValue('Project', 'game_backend')

        self.last_game_backend = self.last_game_backend.lower()

        def run_pygame():
            from .GameBackend import GameBackend_pygame
            self.game_backend = GameBackend_pygame.PyGame(self)
            self.last_game_backend = GameBackNames.PYGAME

        def run_pyglet():
            from .GameBackend import GameBackend_pyglet
            self.game_backend = GameBackend_pyglet.PyGlet(self)
            self.last_game_backend = GameBackNames.PYGLET

        for i in range(GameBackNames.COUNT):
            if self.last_game_backend == GameBackNames.PYGAME:
                try:
                    run_pygame()
                    break
                except:
                    logger.error(traceback.format_exc())
                    logger.error("The pygame library does not exist and execution failed. Run again with the pyglet.")
                    self.last_game_backend = GameBackNames.PYGLET
            else:
                try:
                    run_pyglet()
                    break
                except:
                    logger.error(traceback.format_exc())
                    logger.error("The pyglet library does not exist and execution failed. Run again with the pygame.")
                    self.last_game_backend = GameBackNames.PYGAME
        else:
            logger.error('PyGame or PyGlet is required. Please run "pip install -r requirements.txt" and try again.')
            # send a message to close ui
            if self.uiCmdQueue:
                self.uiCmdQueue.put(COMMAND.CLOSE_UI)
            return False

        self.game_backend.create_window(width, height, full_screen)
        self.opengl_context.initialize()

        if not self.opengl_context.check_gl_version():
            self.is_basic_mode = True
            self.renderer = Renderer_Basic.instance()

        self.send_game_backend_list(self.game_backend_list)
        index = self.game_backend_list.index(self.last_game_backend) if self.last_game_backend in self.game_backend_list else 0
        self.send_current_game_backend_index(index)

        if not self.game_backend.valid:
            self.error('game_backend initializing failed')

        # initialize managers
        self.resource_manager.initialize(self, self.project_manager.project_dir)
        self.viewport_manager.initialize(self)
        if not self.is_basic_mode:
            self.render_option_manager.initialize(self)
            self.rendertarget_manager.initialize(self)
            self.font_manager.initialize(self)
            self.effect_manager.initialize(self)
        self.renderer.initialize(self)
        self.debug_line_manager.initialize(self)
        self.scene_manager.initialize(self)
        self.sound_manager.initialize(self)

        # self.viewport_manager.build_ui_example()

        self.script_manager = None
        # self.load_script_manager(reload=False)

        # new scene
        self.game_backend.reset_screen()
        self.scene_manager.new_scene()

        # test object
        suzan = self.resource_manager.get_model("suzan")
        self.scene_manager.add_object(model=suzan, pos=[0.0, 0.0, -5.0])

        self.send(COMMAND.SORT_UI_ITEMS)
        return True

    def set_window_title(self, title):
        self.game_backend.set_window_title(self.last_game_backend + " - " + title)

    def get_next_open_project_filename(self):
        return self.project_manager.next_open_project_filename

    def load_script_manager(self, reload=True):
        main_script = self.resource_manager.get_script('main')
        if main_script is not None:
            try:
                if reload:
                    self.resource_manager.script_loader.reload()
                self.script_manager = main_script.ScriptManager.instance()
                self.script_manager.initialize(self)
            except:
                logger.error(traceback.format_exc())
        else:
            logger.error("Not found Resource/Scripts/main.py")

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
        self.sound_manager.clear()
        self.project_manager.close_project()
        self.renderer.close()
        self.resource_manager.close()
        self.sound_manager.close()
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
            self.game_backend.set_input_mode(InputMode.GAME_PLAY)
            self.load_script_manager()
        self.commands[COMMAND.PLAY.value] = cmd_play

        def cmd_stop(value):
            self.game_backend.set_input_mode(InputMode.NONE)
            if self.script_manager is not None:
                try:
                    self.script_manager.exit()
                except:
                    logger.error(traceback.format_exc())
        self.commands[COMMAND.STOP.value] = cmd_stop

        # project
        self.commands[COMMAND.NEW_PROJECT.value] = lambda value: self.project_manager.new_project(value)
        self.commands[COMMAND.OPEN_PROJECT.value] = lambda value: self.project_manager.open_project_next_time(value)
        self.commands[COMMAND.SAVE_PROJECT.value] = lambda value: self.project_manager.save_project()
        # scene
        self.commands[COMMAND.NEW_SCENE.value] = lambda value: self.scene_manager.new_scene()
        self.commands[COMMAND.SAVE_SCENE.value] = lambda value: self.scene_manager.save_scene()
        # view mode
        self.commands[COMMAND.VIEWMODE_WIREFRAME.value] = lambda value: self.renderer.set_view_mode(COMMAND.VIEWMODE_WIREFRAME)
        self.commands[COMMAND.VIEWMODE_SHADING.value] = lambda value: self.renderer.set_view_mode(COMMAND.VIEWMODE_SHADING)

        # screen
        def cmd_change_resolution(value):
            width, height, full_screen = value
            self.game_backend.change_resolution(width, height, full_screen)
        self.commands[COMMAND.CHANGE_RESOLUTION.value] = cmd_change_resolution

        # Resource commands
        def cmd_load_resource(value):
            resource_name, resource_type_name = value
            self.resource_manager.load_resource(resource_name, resource_type_name)
        self.commands[COMMAND.LOAD_RESOURCE.value] = cmd_load_resource

        def cmd_action_resource(value):
            resource_name, resource_type_name = value
            self.resource_manager.action_resource(resource_name, resource_type_name)
        self.commands[COMMAND.ACTION_RESOURCE.value] = cmd_action_resource

        def cmd_duplicate_resource(value):
            resource_name, resource_type_name = value
            self.resource_manager.duplicate_resource(resource_name, resource_type_name)
        self.commands[COMMAND.DUPLICATE_RESOURCE.value] = cmd_duplicate_resource

        def cmd_save_resource(value):
            resource_name, resource_type_name = value
            self.resource_manager.save_resource(resource_name, resource_type_name)
        self.commands[COMMAND.SAVE_RESOURCE.value] = cmd_save_resource

        def cmd_delete_resource(value):
            resource_name, resource_type_name = value
            self.resource_manager.delete_resource(resource_name, resource_type_name)
        self.commands[COMMAND.DELETE_RESOURCE.value] = cmd_delete_resource

        def cmd_request_resource_list(value):
            resourceList = self.resource_manager.get_resource_name_and_type_list()
            self.send(COMMAND.TRANS_RESOURCE_LIST, resourceList)
        self.commands[COMMAND.REQUEST_RESOURCE_LIST.value] = cmd_request_resource_list

        def cmd_request_resource_attribute(value):
            resource_name, resource_type_name = value
            attribute = self.resource_manager.get_resource_attribute(resource_name, resource_type_name)
            if attribute:
                self.send(COMMAND.TRANS_RESOURCE_ATTRIBUTE, attribute)
        self.commands[COMMAND.REQUEST_RESOURCE_ATTRIBUTE.value] = cmd_request_resource_attribute

        def cmd_set_resource_attribute(value):
            resource_name, resource_type, attribute_name, attribute_value, item_info_history, attribute_index = value
            self.resource_manager.set_resource_attribute(resource_name,
                                                         resource_type,
                                                         attribute_name,
                                                         attribute_value,
                                                         item_info_history,
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
        self.commands[COMMAND.CREATE_SPLINE.value] = lambda value: self.resource_manager.spline_loader.create_spline()

        def cmd_create_collision(value):
            resource_name, resource_type = value
            if 'Model' == resource_type:
                self.scene_manager.add_collision(name=resource_name, model=resource_name)
        self.commands[COMMAND.CREATE_COLLISION.value] = cmd_create_collision

        self.commands[COMMAND.REQUEST_OBJECT_LIST.value] = lambda value: self.send_object_list()
        self.commands[COMMAND.ACTION_OBJECT.value] = lambda value: self.scene_manager.action_object(value)
        self.commands[COMMAND.DELETE_OBJECT.value] = lambda value: self.scene_manager.delete_object(value)

        def cmd_request_object_attribute(value):
            obj_name, obj_type_name = value
            attribute = self.scene_manager.get_object_attribute(obj_name, obj_type_name)
            if attribute:
                self.send(COMMAND.TRANS_OBJECT_ATTRIBUTE, attribute)
        self.commands[COMMAND.REQUEST_OBJECT_ATTRIBUTE.value] = cmd_request_object_attribute

        def cmd_set_object_attribute(value):
            object_name, object_type, attribute_name, attribute_value, item_info_history, attribute_index = value
            self.scene_manager.set_object_attribute(object_name, object_type, attribute_name, attribute_value, item_info_history, attribute_index)
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
        self.commands[COMMAND.RECREATE_RENDER_TARGETS.value] = cmd_recreate_render_targets

        def cmd_view_rendertarget(value):
            rendertarget_index, rendertarget_name = value
            texture = self.rendertarget_manager.find_rendertarget(rendertarget_index, rendertarget_name)
            self.renderer.set_debug_texture(texture)
            if self.renderer.debug_texture is not None:
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

    def update_command(self):
        if self.uiCmdQueue is None:
            return

        while not self.cmdQueue.empty():
            # receive value must be tuple type
            cmd, value = self.cmdQueue.get()
            self.commands[cmd.value](value)

    def get_window_size(self):
        return self.game_backend.width, self.game_backend.height

    def get_window_width(self):
        return self.game_backend.width

    def get_window_height(self):
        return self.game_backend.height

    def get_mouse_pos(self):
        return self.game_backend.mouse_pos

    def get_mouse_down(self):
        return self.game_backend.get_mouse_down()

    def get_mouse_pressed(self):
        return self.game_backend.get_mouse_pressed()

    def get_mouse_up(self):
        return self.game_backend.get_mouse_up()

    def get_keyboard_pressed(self):
        return self.game_backend.get_keyboard_pressed()

    def is_keyboard_down(self):
        return self.game_backend.keyboard_down

    def is_keyboard_pressed(self):
        return self.game_backend.keyboard_pressed

    def is_keyboard_up(self):
        return self.game_backend.keyboard_up

    def is_key_pressed(self, key_code):
        return self.game_backend.get_keyboard_pressed()[key_code]

    def get_text(self):
        return self.game_backend.text

    def set_render_font(self, value):
        self.render_option.RENDER_FONT = value

    def toggle_render_font(self):
        self.set_render_font(not self.render_option.RENDER_FONT)

    def update_event(self, event_type, event_value=None):
        mouse_delta = self.game_backend.mouse_delta
        key_pressed = self.game_backend.get_keyboard_pressed()
        subkey_down = key_pressed[Keyboard.LCTRL] or key_pressed[Keyboard.LSHIFT] or key_pressed[Keyboard.LALT]
        btn_left, btn_middle, btn_right = self.game_backend.get_mouse_pressed()
        btn_left_up, btn_middle_up, btn_right_up = self.game_backend.get_mouse_up()

        if Event.QUIT == event_type:
            self.close()
        elif Event.VIDEORESIZE == event_type:
            self.video_resized = True
            self.video_resize_time = self.current_time + VIDEO_RESIZE_TIME
            self.notify_change_resolution(event_value)
        elif Event.TEXT == event_type:
            pass

        if Event.KEYUP == event_type:
            if Keyboard.BACKQUOTE == event_value:
                self.toggle_render_font()

        if InputMode.NONE == self.game_backend.get_input_mode():
            if Event.KEYUP == event_type:
                if Keyboard.ESCAPE == event_value:
                    if self.game_backend.full_screen:
                        self.game_backend.change_resolution(0, 0, False)
                    elif self.renderer.debug_texture is not None:
                        self.renderer.set_debug_texture(None)
                    elif self.renderer.postprocess.is_render_shader():
                        self.renderer.postprocess.is_render_material_instance = False
                    elif self.scene_manager.get_selected_object() is not None:
                        self.scene_manager.set_selected_object("")
                    else:
                        self.close()
                elif Keyboard.TAB == event_value:
                    self.game_backend.toggle_mouse_grab()
                elif Keyboard.G == event_value:
                    if self.scene_manager.get_selected_object() is not None:
                        self.game_backend.set_input_mode(InputMode.EDIT_OBJECT_TRANSFORM)
                        self.scene_manager.backup_selected_object_transform()
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
            if Event.MOUSE_MOVE == event_type:
                if self.scene_manager.is_axis_gizmo_drag():
                    self.game_backend.set_input_mode(InputMode.EDIT_OBJECT_TRANSFORM)
            elif btn_left:
                self.scene_manager.intersect_select_object()
        elif InputMode.EDIT_OBJECT_TRANSFORM == self.game_backend.get_input_mode():
            if Event.KEYUP == event_type or Event.MOUSE_BUTTON_UP == event_type:
                if Keyboard.ESCAPE == event_value or btn_right_up:
                    self.game_backend.set_input_mode(InputMode.NONE)
                    self.scene_manager.restore_selected_object_transform()
                if Keyboard.ENTER == event_value or btn_left_up:
                    self.game_backend.set_input_mode(InputMode.NONE)
                    self.scene_manager.clear_selected_axis_gizmo_id()

    def update_camera(self):
        keydown = self.game_backend.get_keyboard_pressed()
        mouse_delta = self.game_backend.mouse_delta
        btn_left, btn_middle, btn_right = self.game_backend.get_mouse_pressed()
        btn_left_up, btn_middle_up, btn_right_up = self.game_backend.get_mouse_up()

        # get camera
        camera = self.scene_manager.main_camera
        camera_transform = camera.transform
        move_speed = camera.move_speed * self.delta
        pan_speed = camera.pan_speed * self.delta

        if keydown[Keyboard.LSHIFT]:
            move_speed *= 4.0
            pan_speed *= 4.0

        # camera move pan
        if btn_middle:
            camera_transform.move_left(-mouse_delta[0] * pan_speed)
            camera_transform.move_up(-mouse_delta[1] * pan_speed)

        # camera rotation
        elif btn_right:
            camera_transform.rotation_pitch(mouse_delta[1] * camera.rotation_speed)
            camera_transform.rotation_yaw(-mouse_delta[0] * camera.rotation_speed)

        if keydown[Keyboard.Z]:
            camera_transform.rotation_roll(-camera.rotation_speed * self.delta)
        elif keydown[Keyboard.C]:
            camera_transform.rotation_roll(camera.rotation_speed * self.delta)

        # move to view direction ( inverse front of camera matrix )
        if keydown[Keyboard.W] or self.game_backend.wheel_up:
            camera_transform.move_front(-move_speed)
        elif keydown[Keyboard.S] or self.game_backend.wheel_down:
            camera_transform.move_front(move_speed)

        # move to side
        if keydown[Keyboard.A]:
            camera_transform.move_left(-move_speed)
        elif keydown[Keyboard.D]:
            camera_transform.move_left(move_speed)

        # move to up
        if keydown[Keyboard.Q]:
            camera_transform.move_up(-move_speed)
        elif keydown[Keyboard.E]:
            camera_transform.move_up(move_speed)

        if keydown[Keyboard.SPACE]:
            camera_transform.reset_transform()

    def update(self):
        current_time = time.perf_counter()
        delta = current_time - self.current_time

        if self.vsync and delta < self.limit_delta or delta == 0.0:
            return

        self.acc_time += delta
        self.frame_count += 1
        self.curr_min_delta = min(delta, self.curr_min_delta)
        self.curr_max_delta = max(delta, self.curr_max_delta)

        # set timer
        self.current_time = current_time
        self.delta = delta
        self.fps = 1.0 / delta

        self.update_time = delta * 1000.0  # millisecond

        start_time = time.perf_counter()

        if self.video_resized and self.video_resize_time < self.current_time:
            self.video_resized = False
            self.video_resize_time = 0
            self.game_backend.resize_scene_to_window()

        touch_event = self.viewport_manager.update(delta)

        self.update_command()

        self.resource_manager.update()

        if not touch_event and self.viewport_manager.main_viewport.collide(*self.get_mouse_pos()):
            if InputMode.GAME_PLAY == self.game_backend.get_input_mode():
                if self.script_manager is not None:
                    try:
                        self.script_manager.update(delta)
                    except:
                        logger.error(traceback.format_exc())
            else:
                self.update_camera()

        self.debug_line_manager.clear_debug_lines()

        self.scene_manager.update_scene(delta)

        self.sound_manager.update(delta)

        # Start Render Scene
        end_time = time.perf_counter()
        self.logic_time = (end_time - start_time) * 1000.0  # millisecond
        start_time = end_time

        if not self.video_resized:
            # render_light_probe scene
            self.renderer.render_light_probe(self.scene_manager.main_light_probe)

            # render sceme
            self.renderer.render_scene()

            # render viewport
            if not self.is_basic_mode:
                self.viewport_manager.render()

            end_time = time.perf_counter()
            self.render_time = (end_time - start_time) * 1000.0  # millisecond
            start_time = end_time

            # end of render scene
            self.opengl_context.present()

            # swap buffer
            self.game_backend.flip()

            end_time = time.perf_counter()
            self.present_time = (end_time - start_time) * 1000.0  # millisecond

        self.acc_logic_time += self.logic_time
        self.acc_gpu_time += self.gpu_time
        self.acc_render_time += self.render_time
        self.acc_present_time += self.present_time

        if 1.0 < self.acc_time:
            self.avg_logic_time = self.acc_logic_time / self.frame_count
            self.avg_gpu_time = self.acc_gpu_time / self.frame_count
            self.avg_render_time = self.acc_render_time / self.frame_count
            self.avg_present_time = self.acc_present_time / self.frame_count

            self.acc_logic_time = 0.0
            self.acc_gpu_time = 0.0
            self.acc_render_time = 0.0
            self.acc_present_time = 0.0

            self.min_delta = self.curr_min_delta * 1000.0
            self.max_delta = self.curr_max_delta * 1000.0
            self.curr_min_delta = sys.float_info.max
            self.curr_max_delta = sys.float_info.min
            self.avg_ms = self.acc_time / self.frame_count * 1000.0
            self.avg_fps = 1000.0 / self.avg_ms
            self.frame_count = 0
            self.acc_time = 0.0

        # debug info
        if not self.is_basic_mode and self.render_option.RENDER_FONT:
            self.font_manager.log("%.2f fps" % self.avg_fps)
            self.font_manager.log("%.2f ms (%.2f ms ~ %.2f ms)" % (self.avg_ms, self.min_delta, self.max_delta))
            self.font_manager.log("CPU : %.2f ms" % self.avg_logic_time)
            self.font_manager.log("GPU : %.2f ms" % self.avg_gpu_time)
            self.font_manager.log("Render : %.2f ms" % self.avg_render_time)
            self.font_manager.log("Present : %.2f ms" % self.avg_present_time)

            render_count = len(self.scene_manager.skeleton_solid_render_infos)
            render_count += len(self.scene_manager.skeleton_translucent_render_infos)
            render_count += len(self.scene_manager.static_solid_render_infos)
            render_count += len(self.scene_manager.static_translucent_render_infos)
            self.font_manager.log("Render Count : %d" % render_count)
            self.font_manager.log("Point Lights : %d" % self.scene_manager.point_light_count)
            self.font_manager.log("Effect Count : %d" % len(self.effect_manager.render_effects))
            self.font_manager.log("Particle Count : %d" % self.effect_manager.alive_particle_count)

            # selected object transform info
            selected_object = self.scene_manager.get_selected_object()
            if selected_object:
                btn_left, btn_middle, btn_right = self.game_backend.get_mouse_pressed()
                if InputMode.NONE == self.game_backend.get_input_mode():
                    if btn_left:
                        self.scene_manager.update_select_object_id()
                elif InputMode.EDIT_OBJECT_TRANSFORM == self.game_backend.get_input_mode():
                    self.scene_manager.edit_selected_object_transform()

                self.font_manager.log("Selected Object : %s" % selected_object.name)
                if hasattr(selected_object, 'transform'):
                    self.font_manager.log(selected_object.transform.get_transform_infos())
        self.gpu_time = (time.perf_counter() - start_time) * 1000.0

        if self.need_to_gc_collect:
            self.need_to_gc_collect = False
            gc.collect()

