import copy
from collections import OrderedDict
import os
import glob
import math

import numpy as np

from PyEngine3D.Common import logger
from PyEngine3D.Common.Constants import *
from PyEngine3D.Render import CollisionActor, StaticActor, SkeletonActor, AxisGizmo
from PyEngine3D.Render import Camera, MainLight, PointLight, LightProbe
from PyEngine3D.Render import gather_render_infos, always_pass, view_frustum_culling_geometry, shadow_culling
from PyEngine3D.Render import Atmosphere, Ocean, Terrain
from PyEngine3D.Render import Effect
from PyEngine3D.Render import Spline3D
from PyEngine3D.Render.RenderOptions import RenderOption
from PyEngine3D.Render.RenderTarget import RenderTargets
from PyEngine3D.Utilities import *


class SceneManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.resource_manager = None
        self.scene_loader = None
        self.renderer = None
        self.effect_manager = None
        self.__current_scene_name = ""

        # Scene Objects
        self.main_camera = None
        self.main_light = None
        self.main_light_probe = None

        self.selected_object = None
        self.selected_object_transform = TransformObject()
        self.selected_object_id = 0

        self.selected_spline_point_gizmo_id = None
        self.selected_spline_control_point_gizmo_id = None
        self.spline_control_point_gizmo_id0 = None
        self.spline_control_point_gizmo_id1 = None
        self.spline_gizmo_object_map = {}

        self.selected_axis_gizmo_id = None
        self.axis_gizmo = None

        # envirment object
        self.atmosphere = None
        self.ocean = None
        self.terrain = None

        self.cameras = []
        self.point_lights = []
        self.light_probes = []
        self.collision_actors = []
        self.static_actors = []
        self.skeleton_actors = []
        self.objectMap = {}  # All of objects
        self.objectIDMap = {}
        self.objectIDEntry = list(range(2 ** 16))
        self.objectIDCounter = AxisGizmo.ID_COUNT

        # render group
        self.point_light_count = 0

        self.static_solid_render_infos = []
        self.static_translucent_render_infos = []
        self.static_shadow_render_infos = []
        self.skeleton_solid_render_infos = []
        self.skeleton_translucent_render_infos = []
        self.skeleton_shadow_render_infos = []

        self.axis_gizmo_render_infos = []
        self.spline_gizmo_render_infos = []

    def initialize(self, core_manager):
        logger.info("initialize " + GetClassName(self))
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.scene_loader = self.resource_manager.scene_loader
        self.renderer = core_manager.renderer
        self.effect_manager = core_manager.effect_manager
        self.axis_gizmo = AxisGizmo(name='axis_gizmo', model=self.resource_manager.get_model('axis_gizmo'))

    def get_current_scene_name(self):
        return self.__current_scene_name

    def set_current_scene_name(self, scene_name):
        self.__current_scene_name = scene_name
        self.core_manager.set_window_title(scene_name)

    def clear_scene(self):
        self.core_manager.notify_clear_scene()
        self.clear_selected_object()
        self.clear_spline_gizmo()
        self.clear_selected_axis_gizmo_id()
        self.effect_manager.clear()
        self.main_camera = None
        self.main_light = None
        self.main_light_probe = None
        self.selected_object = None
        self.selected_object_id = 0
        self.selected_axis_gizmo_id = None
        self.cameras = []
        self.point_lights = []
        self.light_probes = []
        self.collision_actors = []
        self.static_actors = []
        self.skeleton_actors = []
        self.splines = []

        self.objectMap = {}
        self.objectIDMap = {}
        self.objectIDEntry = list(range(2 ** 16))

        self.static_solid_render_infos = []
        self.static_translucent_render_infos = []
        self.static_shadow_render_infos = []
        self.skeleton_solid_render_infos = []
        self.skeleton_translucent_render_infos = []
        self.skeleton_shadow_render_infos = []
        self.selected_object_render_info = []
        self.spline_gizmo_render_infos = []

        self.renderer.set_debug_texture(None)

    def begin_open_scene(self):
        self.clear_scene()

    def end_open_scene(self):
        self.update_scene(0.0)
        self.renderer.reset_renderer()
        self.regist_object(self.renderer.postprocess)

        # Important : update camera projection
        for camera in self.cameras:
            camera.update()

    def new_scene(self):
        self.begin_open_scene()

        # add scene objects
        self.main_camera = self.add_camera()
        self.main_light = self.add_main_light()
        self.main_light_probe = self.add_light_probe(pos=[0.0, 5.0, 0.0])
        self.atmosphere = self.add_atmosphere()
        self.ocean = self.add_ocean()
        self.terrain = self.add_terrain()

        self.set_current_scene_name(self.resource_manager.scene_loader.get_new_resource_name("new_scene"))

        logger.info("New scene : %s" % self.__current_scene_name)

        scene_data = self.get_save_data()
        self.resource_manager.scene_loader.create_resource(self.__current_scene_name, scene_data)

        self.end_open_scene()

    def open_scene(self, scene_name, scene_data):
        self.begin_open_scene()

        self.set_current_scene_name(scene_name)

        logger.info("Open scene : %s" % scene_name)

        camera_datas = scene_data.get('cameras', [])
        for camera_data in camera_datas:
            self.add_camera(**camera_data)
        self.main_camera = self.cameras[0] if 0 < len(self.cameras) else None

        main_light_data = scene_data.get('main_light', None)
        if main_light_data is not None:
            self.main_light = self.add_main_light(**main_light_data)
        else:
            self.main_light = self.add_main_light()

        light_datas = scene_data.get('lights', [])
        for light_data in light_datas:
            self.add_light(**light_data)

        light_probe_datas = scene_data.get('light_probes', [])
        if light_probe_datas:
            for light_probe_data in light_probe_datas:
                self.add_light_probe(**light_probe_data)
        else:
            self.add_light_probe()
        self.main_light_probe = self.light_probes[0] if 0 < len(self.light_probes) else None

        spline_datas = scene_data.get('splines', [])
        for spline_data in spline_datas:
            self.add_spline(**spline_data)

        atmosphere_data = scene_data.get('atmosphere', {})
        self.atmosphere = self.add_atmosphere(**atmosphere_data)

        ocean_data = scene_data.get('ocean', {})
        self.ocean = self.add_ocean(**ocean_data)

        terrain_data = scene_data.get('terrain', {})
        self.terrain = self.add_terrain(**terrain_data)

        for collision_data in scene_data.get('collision_actors', []):
            self.add_collision(**collision_data)

        for object_data in scene_data.get('static_actors', []):
            self.add_object(**object_data)

        for object_data in scene_data.get('skeleton_actors', []):
            self.add_object(**object_data)

        for effect_data in scene_data.get('effects', []):
            self.add_effect(**effect_data)

        self.end_open_scene()

    def save_scene(self):
        if self.__current_scene_name == "":
            self.set_current_scene_name(self.resource_manager.scene_loader.get_new_resource_name("new_scene"))
        self.resource_manager.scene_loader.save_resource(self.__current_scene_name)

    def get_save_data(self):
        scene_data = dict(
            cameras=[camera.get_save_data() for camera in self.cameras],
            main_light=self.main_light.get_save_data() if self.main_light is not None else dict(),
            lights=[light.get_save_data() for light in self.point_lights],
            light_probes=[light_probe.get_save_data() for light_probe in self.light_probes],
            splines=[spline.get_save_data() for spline in self.splines],
            atmosphere=self.atmosphere.get_save_data(),
            ocean=self.ocean.get_save_data(),
            terrain=self.terrain.get_save_data(),
            collision_actors=[collision_actor.get_save_data() for collision_actor in self.collision_actors],
            static_actors=[static_actor.get_save_data() for static_actor in self.static_actors],
            skeleton_actors=[skeleton_actor.get_save_data() for skeleton_actor in self.skeleton_actors],
            effects=self.effect_manager.get_save_data()
        )
        return scene_data

    def generate_object_name(self, currName):
        index = 0
        if currName in self.objectMap:
            while True:
                newName = "%s_%d" % (currName, index)
                if newName not in self.objectMap:
                    return newName
                index += 1
        return currName

    def get_object_list(self, object_type):
        if Camera == object_type:
            return self.cameras
        elif PointLight == object_type:
            return self.point_lights
        elif LightProbe == object_type:
            return self.light_probes
        elif CollisionActor == object_type:
            return self.collision_actors
        elif StaticActor == object_type:
            return self.static_actors
        elif SkeletonActor == object_type:
            return self.skeleton_actors
        elif Spline3D == object_type:
            return self.splines
        return None

    def generate_object_id(self):
        object_id = self.objectIDEntry[self.objectIDCounter]
        self.objectIDCounter += 1
        return object_id

    def restore_object_id(self, object_id):
        if 0 < self.objectIDCounter:
            self.objectIDCounter -= 1
            self.objectIDEntry[self.objectIDCounter] = object_id

    def regist_object(self, obj):
        if obj is not None and obj.name not in self.objectMap:
            object_type = type(obj)
            object_list = self.get_object_list(object_type)
            if object_list is not None:
                object_list.append(obj)
            elif object_type is Effect:
                self.effect_manager.add_effect(obj)
            if hasattr(obj, 'set_object_id'):
                object_id = self.generate_object_id()
                obj.set_object_id(object_id)
                self.objectIDMap[object_id] = obj
            self.objectMap[obj.name] = obj
            self.core_manager.send_object_info(obj)
        else:
            logger.error("SceneManager::regist_object error. %s" % obj.name if obj else 'None')

    def unregist_resource(self, obj):
        if obj is not None and obj.name in self.objectMap:
            object_type = type(obj)
            object_list = self.get_object_list(object_type)
            if object_list is not None:
                object_list.remove(obj)
            elif object_type is Effect:
                self.effect_manager.delete_effect(obj)

            self.objectMap.pop(obj.name)

            if hasattr(obj, 'get_object_id'):
                object_id = obj.get_object_id()
                self.restore_object_id(object_id)
                if AxisGizmo.ID_COUNT <= object_id:
                    self.objectIDMap.pop(object_id)

            self.core_manager.notify_delete_object(obj.name)

            if self.selected_object is obj and hasattr(self.selected_object, "set_selected"):
                obj.set_selected(False)
                self.selected_object = None

            if hasattr(obj, 'delete'):
                obj.delete()
        else:
            logger.error("SceneManager::unregist_resource error. %s" % obj.name if obj else 'None')

    def add_camera(self, **camera_data):
        name = self.generate_object_name(camera_data.get('name', 'camera'))
        camera_data['name'] = name
        camera_data['model'] = self.resource_manager.get_model('Cube')
        logger.info("add Camera : %s" % name)
        camera = Camera(scene_manager=self, **camera_data)
        camera.initialize()
        self.regist_object(camera)
        return camera

    def add_main_light(self, **light_data):
        name = self.generate_object_name(light_data.get('name', 'main_light'))
        light_data['name'] = name
        light_data['model'] = self.resource_manager.get_model('Cube')
        logger.info("add MainLight : %s" % name)
        light = MainLight(**light_data)
        self.regist_object(light)
        return light

    def add_light(self, **light_data):
        name = self.generate_object_name(light_data.get('name', 'light'))
        light_data['name'] = name
        light_data['model'] = self.resource_manager.get_model('Cube')
        logger.info("add Light : %s" % name)
        light = PointLight(**light_data)
        self.regist_object(light)
        return light

    def add_light_probe(self, **light_probe_data):
        name = self.generate_object_name(light_probe_data.get('name', 'light_probe'))
        light_probe_data['name'] = name
        light_probe_data['model'] = self.resource_manager.get_model('Cube')
        logger.info("add Light Probe : %s" % name)
        light_probe = LightProbe(**light_probe_data)
        self.regist_object(light_probe)
        return light_probe

    def add_spline_here(self, **spline_data):
        spline_data['pos'] = self.main_camera.transform.pos - self.main_camera.transform.front * 10.0
        self.add_spline(**spline_data)

    def add_spline(self, **spline_data):
        name = self.generate_object_name(spline_data.get('name', 'spline'))
        spline_data['name'] = name
        spline_data['spline_data'] = self.resource_manager.get_spline(spline_data.get('spline_data', ''))
        logger.info("add Spline : %s" % name)
        spline = Spline3D(**spline_data)
        self.regist_object(spline)
        return spline

    def create_spline_gizmo(self, spline):
        spline_point_name = spline.name + '_point'
        control_point_name = spline.name + '_control_point'
        gizmo_model = self.resource_manager.get_model('Cube')
        if len(spline.spline_data.spline_points) < 1:
            return

        for spline_point in spline.spline_data.spline_points:
            pos = np.dot(Float4(*spline_point.position, 1.0), spline.transform.matrix)[:3]
            gizmo_object = StaticActor(name=spline_point_name, model=gizmo_model, pos=Float3(*pos), scale=Float3(0.1, 0.1, 0.1), object_id=self.generate_object_id(), object_color=Float3(0.5, 0.5, 1.0))
            self.spline_gizmo_object_map[gizmo_object.get_object_id()] = gizmo_object

        spline_point = spline.spline_data.spline_points[0]

        def create_spline_control_point_gizmo(spline_gizmo_object_map, object_id, inverse):
            if inverse:
                pos = np.dot(Float4(*(spline_point.position + spline_point.control_point), 1.0), spline.transform.matrix)[:3]
            else:
                pos = np.dot(Float4(*(spline_point.position - spline_point.control_point), 1.0), spline.transform.matrix)[:3]
            gizmo_object = StaticActor(name=control_point_name, model=gizmo_model, pos=Float3(*pos), scale=Float3(0.075, 0.075, 0.075), object_id=object_id, object_color=Float3(0.0, 1.0, 0.0))
            spline_gizmo_object_map[gizmo_object.get_object_id()] = gizmo_object
            return gizmo_object.get_object_id()
        self.spline_control_point_gizmo_id0 = create_spline_control_point_gizmo(self.spline_gizmo_object_map, self.generate_object_id(), inverse=False)
        self.spline_control_point_gizmo_id1 = create_spline_control_point_gizmo(self.spline_gizmo_object_map, self.generate_object_id(), inverse=True)

        # select first spline gizmo object
        # self.set_selected_spline_gizmo_id(list(self.spline_gizmo_object_map.keys())[0])

        gather_render_infos(culling_func=always_pass,
                            camera=self.main_camera,
                            light=self.main_light,
                            actor_list=self.spline_gizmo_object_map.values(),
                            solid_render_infos=self.spline_gizmo_render_infos,
                            translucent_render_infos=None)

    def set_selected_spline_gizmo_id(self, spline_gizmo_id):
        if spline_gizmo_id == self.spline_control_point_gizmo_id0 or spline_gizmo_id == self.spline_control_point_gizmo_id1:
            self.selected_spline_control_point_gizmo_id = spline_gizmo_id
        else:
            self.selected_spline_control_point_gizmo_id = None
            self.selected_spline_point_gizmo_id = spline_gizmo_id

    def clear_spline_gizmo(self):
        self.selected_spline_point_gizmo_id = None
        self.selected_spline_control_point_gizmo_id = None
        self.spline_control_point_gizmo_id0 = None
        self.spline_control_point_gizmo_id1 = None
        for spline_gizmo_object_id in self.spline_gizmo_object_map:
            self.restore_object_id(self.spline_gizmo_object_map[spline_gizmo_object_id].get_object_id())
        self.spline_gizmo_object_map.clear()
        self.spline_gizmo_render_infos.clear()

    def clear_selected_axis_gizmo_id(self):
        self.selected_axis_gizmo_id = None

    def is_axis_gizmo_drag(self):
        return self.selected_axis_gizmo_id is not None

    def add_effect_here(self, **effect_data):
        effect_data['pos'] = self.main_camera.transform.pos - self.main_camera.transform.front * 10.0
        self.add_effect(**effect_data)

    def add_effect(self, **effect_data):
        name = self.generate_object_name(effect_data.get('name', 'effect'))
        logger.info("add Particle : %s" % name)
        effect_data['name'] = name
        effect_data['effect_info'] = self.resource_manager.get_effect(effect_data.get('effect_info', ''))
        effect = Effect(**effect_data)
        self.regist_object(effect)
        return effect

    def add_atmosphere(self, **atmosphere_data):
        atmosphere_data['name'] = self.generate_object_name(atmosphere_data.get('name', 'atmosphere'))
        logger.info("add Atmosphere : %s" % atmosphere_data['name'])
        atmosphere = Atmosphere(**atmosphere_data)
        if not self.core_manager.is_basic_mode:
            atmosphere.initialize()
        self.regist_object(atmosphere)
        return atmosphere

    def add_ocean(self, **object_data):
        object_data['name'] = self.generate_object_name(object_data.get('name', 'ocean'))
        logger.info("add Ocean : %s" % object_data['name'])
        ocean = Ocean(**object_data)
        if not self.core_manager.is_basic_mode:
            ocean.initialize()
        self.regist_object(ocean)
        return ocean

    def add_terrain(self, **object_data):
        object_data['name'] = self.generate_object_name(object_data.get('name', 'terrain'))
        logger.info("add Terrain : %s" % object_data['name'])
        terrain = Terrain(**object_data)
        if not self.core_manager.is_basic_mode:
            terrain.initialize()
        self.regist_object(terrain)
        return terrain

    def add_object(self, **object_data):
        model = object_data.get('model')
        if model:
            object_data['name'] = self.generate_object_name(object_data.get('name', model.name))
            objType = GetClassName(model)
            logger.info("add %s : %s" % (objType, object_data['name']))

            if model.mesh and model.mesh.has_bone():
                obj_instance = SkeletonActor(**object_data)
            else:
                obj_instance = StaticActor(**object_data)
            # regist
            self.regist_object(obj_instance)
            return obj_instance
        return None

    def add_object_here(self, model):
        pos = self.main_camera.transform.pos - self.main_camera.transform.front * 10.0
        return self.add_object(model=model, pos=pos)

    def add_collision(self, **collision_data):
        name = self.generate_object_name(collision_data.get('name', 'collision'))
        mesh = self.resource_manager.get_model(collision_data.get('model'))
        if mesh is not None:
            collision_data['name'] = name
            collision_data['model'] = mesh
            logger.info("add Collision : %s" % name)
            collision = CollisionActor(**collision_data)
            self.regist_object(collision)
            return collision
        return None

    def clear_objects(self):
        self.cameras = []
        self.point_lights = []
        self.collision_actors = []
        self.static_actors = []
        self.skeleton_actors = []
        self.splines = []
        self.objectMap = {}

    def clear_actors(self):
        for obj_name in list(self.objectMap.keys()):
            self.delete_object(obj_name)

    def action_object(self, object_name):
        obj = self.get_object(object_name)
        if obj is not None:
            object_type = type(obj)
            if LightProbe == object_type:
                self.renderer.set_debug_texture(obj.texture_probe)
                self.core_manager.send_object_attribute(obj.texture_probe.get_attribute())

    def delete_object(self, object_name):
        obj = self.get_object(object_name)
        logger.info("delete %s : %s" % (type(obj), object_name))
        if obj is not None and obj not in (self.main_camera, self.main_light, self.main_light_probe):
            self.unregist_resource(obj)

    def get_axis_gizmo(self):
        return self.axis_gizmo

    def get_object(self, object_name):
        return self.objectMap.get(object_name)

    def get_object_names(self):
        return self.objectMap.keys()

    def get_objects(self):
        return self.objectMap.values()

    def get_light_probe_texture(self):
        if RenderOption.RENDER_LIGHT_PROBE:
            return RenderTargets.LIGHT_PROBE_ATMOSPHERE
        return self.main_light_probe.texture_probe

    def reset_light_probe(self):
        for light_probe in self.light_probes:
            light_probe.isRendered = False

    def get_object_attribute(self, object_name, objectTypeName):
        obj = self.get_object(object_name)
        return obj.get_attribute() if obj else None

    def set_object_attribute(self, object_name, objectTypeName, attribute_name, attribute_value, item_info_history, attribute_index):
        obj = self.get_object(object_name)
        obj and obj.set_attribute(attribute_name, attribute_value, item_info_history, attribute_index)

    def get_selected_object_id(self):
        return self.selected_object_id

    def set_selected_object_id(self, object_id):
        self.selected_object_id = object_id

    def clear_selected_object(self):
        self.selected_object = None
        self.selected_object_id = 0

    def get_selected_object(self):
        return self.selected_object

    def set_selected_object(self, object_name):
        selected_object = self.get_object(object_name)
        if self.selected_object is not selected_object:
            self.clear_selected_axis_gizmo_id()
            self.clear_spline_gizmo()
            self.selected_object_render_info = []

            if self.selected_object and hasattr(self.selected_object, "set_selected"):
                self.selected_object.set_selected(False)

            # set selected object
            self.selected_object = selected_object
            if selected_object is not None:
                if hasattr(selected_object, "get_object_id"):
                    self.set_selected_object_id(selected_object.get_object_id())

                if hasattr(selected_object, "set_selected"):
                    selected_object.set_selected(True)

                if type(selected_object) in (SkeletonActor, StaticActor):
                    gather_render_infos(culling_func=always_pass,
                                        camera=self.main_camera,
                                        light=self.main_light,
                                        actor_list=[self.selected_object, ],
                                        solid_render_infos=self.selected_object_render_info,
                                        translucent_render_infos=self.selected_object_render_info)
                elif type(selected_object) is Spline3D:
                    self.create_spline_gizmo(selected_object)

    def backup_selected_object_transform(self):
        if self.selected_object and hasattr(self.selected_object, "transform"):
            self.selected_object_transform.clone(self.selected_object.transform)

    def restore_selected_object_transform(self):
        if self.selected_object and hasattr(self.selected_object, "transform"):
            self.selected_object.transform.clone(self.selected_object_transform)

    def edit_selected_object_transform(self):
        selected_spline_control_point_gizmo_object = self.spline_gizmo_object_map.get(self.selected_spline_control_point_gizmo_id)
        selected_spline_point_gizmo_object = self.spline_gizmo_object_map.get(self.selected_spline_point_gizmo_id)
        edit_object = selected_spline_control_point_gizmo_object or selected_spline_point_gizmo_object or self.selected_object
        if edit_object is None:
            return

        mouse_delta = self.core_manager.game_backend.mouse_delta
        if any(0.0 != mouse_delta):
            mouse_pos = self.core_manager.game_backend.mouse_pos
            mouse_pos_old = self.core_manager.game_backend.mouse_pos_old
            camera = self.main_camera
            camera_transform = camera.transform
            screen_width = self.core_manager.viewport_manager.main_viewport.width
            screen_height = self.core_manager.viewport_manager.main_viewport.height
            edit_object_transform = edit_object.transform
            use_quaternion = False

            mouse_x_ratio = mouse_pos[0] / screen_width
            mouse_y_ratio = mouse_pos[1] / screen_height
            mouse_x_ratio_old = mouse_pos_old[0] / screen_width
            mouse_y_ratio_old = mouse_pos_old[1] / screen_height
            mouse_world_pos = np.dot(Float4(mouse_x_ratio * 2.0 - 1.0, mouse_y_ratio * 2.0 - 1.0, 0.0, 1.0), camera.inv_view_origin_projection)
            mouse_world_pos_old = np.dot(Float4(mouse_x_ratio_old * 2.0 - 1.0, mouse_y_ratio_old * 2.0 - 1.0, 0.0, 1.0), camera.inv_view_origin_projection)

            to_object = edit_object_transform.get_pos() - camera_transform.get_pos()
            to_object_xz_dist = length(Float2(to_object[0], to_object[2]))
            mouse_xz_dist = length(Float2(mouse_world_pos[0], mouse_world_pos[2]))
            mouse_xz_dist_old = length(Float2(mouse_world_pos_old[0], mouse_world_pos_old[2]))

            if AxisGizmo.ID_POSITION_X == self.selected_axis_gizmo_id:
                edit_object_transform.move_x((mouse_world_pos[0] * to_object[2] / mouse_world_pos[2]) - (mouse_world_pos_old[0] * to_object[2] / mouse_world_pos_old[2]))
            elif AxisGizmo.ID_POSITION_Y == self.selected_axis_gizmo_id:
                edit_object_transform.move_y((mouse_world_pos[1] * to_object_xz_dist / mouse_xz_dist) - (mouse_world_pos_old[1] * to_object_xz_dist / mouse_xz_dist_old))
            elif AxisGizmo.ID_POSITION_Z == self.selected_axis_gizmo_id:
                edit_object_transform.move_z((mouse_world_pos[2] * to_object[0] / mouse_world_pos[0]) - (mouse_world_pos_old[2] * to_object[0] / mouse_world_pos_old[0]))
            elif AxisGizmo.ID_POSITION_XY == self.selected_axis_gizmo_id:
                edit_object_transform.move_x((mouse_world_pos[0] * to_object[2] / mouse_world_pos[2]) - (mouse_world_pos_old[0] * to_object[2] / mouse_world_pos_old[2]))
                edit_object_transform.move_y((mouse_world_pos[1] * to_object_xz_dist / mouse_xz_dist) - (mouse_world_pos_old[1] * to_object_xz_dist / mouse_xz_dist_old))
            elif AxisGizmo.ID_POSITION_XZ == self.selected_axis_gizmo_id:
                edit_object_transform.move_x((mouse_world_pos[0] * to_object[1] / mouse_world_pos[1]) - (mouse_world_pos_old[0] * to_object[1] / mouse_world_pos_old[1]))
                edit_object_transform.move_z((mouse_world_pos[2] * to_object[1] / mouse_world_pos[1]) - (mouse_world_pos_old[2] * to_object[1] / mouse_world_pos_old[1]))
            elif AxisGizmo.ID_POSITION_YZ == self.selected_axis_gizmo_id:
                edit_object_transform.move_y((mouse_world_pos[1] * to_object_xz_dist / mouse_xz_dist) - (mouse_world_pos_old[1] * to_object_xz_dist / mouse_xz_dist_old))
                edit_object_transform.move_z((mouse_world_pos[2] * to_object[0] / mouse_world_pos[0]) - (mouse_world_pos_old[2] * to_object[0] / mouse_world_pos_old[0]))
            elif AxisGizmo.ID_ROTATION_PITCH == self.selected_axis_gizmo_id:
                yz = Float2(mouse_world_pos[1] * to_object[0] / mouse_world_pos[0], mouse_world_pos[2] * to_object[0] / mouse_world_pos[0]) - Float2(to_object[1], to_object[2])
                yz_old = Float2(mouse_world_pos_old[1] * to_object[0] / mouse_world_pos_old[0], mouse_world_pos_old[2] * to_object[0] / mouse_world_pos_old[0]) - Float2(to_object[1], to_object[2])
                if use_quaternion:
                    quat = axis_rotation(edit_object_transform.left, math.atan2(yz[1], yz[0]) - math.atan2(yz_old[1], yz_old[0]))
                    edit_object_transform.multiply_quaternion(quat)
                else:
                    edit_object_transform.rotation_pitch(math.atan2(yz[1], yz[0]) - math.atan2(yz_old[1], yz_old[0]))
            elif AxisGizmo.ID_ROTATION_YAW == self.selected_axis_gizmo_id:
                xz = Float2(mouse_world_pos[0] * to_object[1] / mouse_world_pos[1], mouse_world_pos[2] * to_object[1] / mouse_world_pos[1]) - Float2(to_object[0], to_object[2])
                xz_old = Float2(mouse_world_pos_old[0] * to_object[1] / mouse_world_pos_old[1], mouse_world_pos_old[2] * to_object[1] / mouse_world_pos_old[1]) - Float2(to_object[0], to_object[2])
                if use_quaternion:
                    quat = axis_rotation(edit_object_transform.up, math.atan2(xz_old[1], xz_old[0]) - math.atan2(xz[1], xz[0]))
                    edit_object_transform.multiply_quaternion(quat)
                else:
                    edit_object_transform.rotation_yaw(math.atan2(xz_old[1], xz_old[0]) - math.atan2(xz[1], xz[0]))
            elif AxisGizmo.ID_ROTATION_ROLL == self.selected_axis_gizmo_id:
                xy = Float2(mouse_world_pos[0] * to_object[2] / mouse_world_pos[2], mouse_world_pos[1] * to_object[2] / mouse_world_pos[2]) - Float2(to_object[0], to_object[1])
                xy_old = Float2(mouse_world_pos_old[0] * to_object[2] / mouse_world_pos_old[2], mouse_world_pos_old[1] * to_object[2] / mouse_world_pos_old[2]) - Float2(to_object[0], to_object[1])
                if use_quaternion:
                    quat = axis_rotation(edit_object_transform.front, math.atan2(xy[1], xy[0]) - math.atan2(xy_old[1], xy_old[0]))
                    edit_object_transform.multiply_quaternion(quat)
                else:
                    edit_object_transform.rotation_roll(math.atan2(xy[1], xy[0]) - math.atan2(xy_old[1], xy_old[0]))
            elif AxisGizmo.ID_SCALE_X == self.selected_axis_gizmo_id:
                edit_object_transform.scale_x(((mouse_world_pos[0] * to_object[2] / mouse_world_pos[2]) - (mouse_world_pos_old[0] * to_object[2] / mouse_world_pos_old[2])))
            elif AxisGizmo.ID_SCALE_Y == self.selected_axis_gizmo_id:
                edit_object_transform.scale_y((mouse_world_pos[1] * to_object_xz_dist / mouse_xz_dist) - (mouse_world_pos_old[1] * to_object_xz_dist / mouse_xz_dist_old))
            elif AxisGizmo.ID_SCALE_Z == self.selected_axis_gizmo_id:
                edit_object_transform.scale_z((mouse_world_pos[2] * to_object[0] / mouse_world_pos[0]) - (mouse_world_pos_old[2] * to_object[0] / mouse_world_pos_old[0]))
            else:
                d0 = np.dot(-camera_transform.front, to_object)
                d1 = np.dot(-camera_transform.front, mouse_world_pos[0:3])
                pos = (mouse_world_pos[0:3] / d1 * d0) - to_object
                edit_object_transform.move(pos)

            # update_spline_gizmo_object
            if selected_spline_point_gizmo_object is not None and self.selected_object is not None:
                spline_index = list(self.spline_gizmo_object_map).index(self.selected_spline_point_gizmo_id)
                spline_point = self.selected_object.spline_data.spline_points[spline_index]
                spline_point_gizmo_pos = np.dot(Float4(*selected_spline_point_gizmo_object.transform.get_pos(), 1.0), self.selected_object.transform.inverse_matrix)[:3]
                spline_point.position[...] = spline_point_gizmo_pos
                if selected_spline_control_point_gizmo_object is not None:
                    spline_control_point_gizmo_pos = np.dot(Float4(*selected_spline_control_point_gizmo_object.transform.get_pos(), 1.0), self.selected_object.transform.inverse_matrix)[:3]
                    if self.spline_control_point_gizmo_id0 == self.selected_spline_control_point_gizmo_id:
                        spline_point.control_point[...] = spline_point_gizmo_pos - spline_control_point_gizmo_pos
                    elif self.spline_control_point_gizmo_id1 == self.selected_spline_control_point_gizmo_id:
                        spline_point.control_point[...] = spline_control_point_gizmo_pos - spline_point_gizmo_pos
                self.selected_object.spline_data.resampling()

    def update_select_object_id(self):
        windows_size = self.core_manager.get_window_size()
        mouse_pos = self.core_manager.get_mouse_pos()
        x = math.floor(min(1.0, (mouse_pos[0] / windows_size[0])) * (RenderTargets.OBJECT_ID.width - 1))
        y = math.floor(min(1.0, (mouse_pos[1] / windows_size[1])) * (RenderTargets.OBJECT_ID.height - 1))
        object_ids = RenderTargets.OBJECT_ID.get_image_data()
        object_id = math.floor(object_ids[y][x] + 0.5)
        return object_id

    def intersect_select_object(self):
        object_id = self.update_select_object_id()
        if 0 < object_id:
            if object_id < AxisGizmo.ID_COUNT:
                self.selected_axis_gizmo_id = object_id
            elif object_id in self.spline_gizmo_object_map:
                self.set_selected_spline_gizmo_id(object_id)
            else:
                obj = self.objectIDMap.get(object_id)
                if obj is not None:
                    self.set_selected_object(obj.name)
        else:
            self.set_selected_object("")

    def set_object_focus(self, object_name):
        obj = self.get_object(object_name)
        if obj and obj != self.main_camera:
            self.main_camera.transform.set_pos(obj.transform.pos - self.main_camera.transform.front * 2.0)

    def update_camera_projection_matrix(self, fov=0.0, aspect=0.0):
        for camera in self.cameras:
            camera.update_projection(fov, aspect)

    def update_static_render_info(self):
        self.static_solid_render_infos = []
        self.static_translucent_render_infos = []
        self.static_shadow_render_infos = []

        if RenderOption.RENDER_COLLISION:
            gather_render_infos(culling_func=view_frustum_culling_geometry,
                                camera=self.main_camera,
                                light=self.main_light,
                                actor_list=self.collision_actors,
                                solid_render_infos=self.static_solid_render_infos,
                                translucent_render_infos=self.static_translucent_render_infos)

        if RenderOption.RENDER_STATIC_ACTOR:
            gather_render_infos(culling_func=view_frustum_culling_geometry,
                                camera=self.main_camera,
                                light=self.main_light,
                                actor_list=self.static_actors,
                                solid_render_infos=self.static_solid_render_infos,
                                translucent_render_infos=self.static_translucent_render_infos)

            gather_render_infos(culling_func=shadow_culling,
                                camera=self.main_camera,
                                light=self.main_light,
                                actor_list=self.static_actors,
                                solid_render_infos=self.static_shadow_render_infos,
                                translucent_render_infos=None)

        self.static_solid_render_infos.sort(key=lambda x: (id(x.geometry), id(x.material)))
        self.static_translucent_render_infos.sort(key=lambda x: (id(x.geometry), id(x.material)))

    def update_skeleton_render_info(self):
        self.skeleton_solid_render_infos = []
        self.skeleton_translucent_render_infos = []
        self.skeleton_shadow_render_infos = []

        if RenderOption.RENDER_SKELETON_ACTOR:
            gather_render_infos(culling_func=view_frustum_culling_geometry,
                                camera=self.main_camera,
                                light=self.main_light,
                                actor_list=self.skeleton_actors,
                                solid_render_infos=self.skeleton_solid_render_infos,
                                translucent_render_infos=self.skeleton_translucent_render_infos)

            gather_render_infos(culling_func=shadow_culling,
                                camera=self.main_camera,
                                light=self.main_light,
                                actor_list=self.skeleton_actors,
                                solid_render_infos=self.skeleton_shadow_render_infos,
                                translucent_render_infos=None)

            self.skeleton_solid_render_infos.sort(key=lambda x: (id(x.geometry), id(x.material)))
            self.skeleton_translucent_render_infos.sort(key=lambda x: (id(x.geometry), id(x.material)))

    def update_light_render_infos(self):
        self.point_light_count = 0
        self.renderer.uniform_point_light_data.fill(0.0)

        for point_light in self.point_lights:
            to_light = point_light.transform.pos - self.main_camera.transform.pos
            for i in range(4):
                d = np.dot(self.main_camera.frustum_vectors[i], to_light)
                if point_light.light_radius < d:
                    # culling
                    break
            else:
                # pass culling
                point_light_uniform_block = self.renderer.uniform_point_light_data[self.point_light_count]
                point_light_uniform_block['color'] = point_light.light_color
                point_light_uniform_block['radius'] = point_light.light_radius
                point_light_uniform_block['pos'] = point_light.transform.pos
                point_light_uniform_block['render'] = 1.0
                self.point_light_count += 1
            if MAX_POINT_LIGHTS <= self.point_light_count:
                break

    def update_scene(self, dt):
        if not self.core_manager.is_basic_mode:
            self.renderer.postprocess.update()

        for camera in self.cameras:
            camera.update()

        if self.main_light is not None:
            self.main_light.update(self.main_camera)

            if self.main_light.changed:
                self.main_light.reset_changed()
                self.reset_light_probe()

        for light in self.point_lights:
            light.update()

        for collision_actor in self.collision_actors:
            collision_actor.update(dt)

        for static_actor in self.static_actors:
            static_actor.update(dt)

        for skeleton_actor in self.skeleton_actors:
            skeleton_actor.update(dt)

        for spline in self.splines:
            spline.update(dt)

        if not self.core_manager.is_basic_mode:
            self.atmosphere.update(self.main_light)
            self.ocean.update(dt)

            if self.terrain.is_render_terrain:
                self.terrain.update(dt)

            self.effect_manager.update(dt)

        # culling
        self.update_static_render_info()
        self.update_skeleton_render_info()
        self.update_light_render_infos()

        if self.selected_object is not None and hasattr(self.selected_object, 'transform'):
            # update spline gizmo objects
            spline_point_gizmo_object = self.spline_gizmo_object_map.get(self.selected_spline_point_gizmo_id)
            if 0 < len(self.spline_gizmo_object_map):
                spline_gizmo_position = Float3(0.0, 0.0, 0.0)
                for spline_gizmo_object_id in self.spline_gizmo_object_map:
                    spline_gizmo_object = self.spline_gizmo_object_map[spline_gizmo_object_id]
                    # spline control point gizmo
                    if spline_gizmo_object_id in (self.spline_control_point_gizmo_id0, self.spline_control_point_gizmo_id1):
                        if self.selected_spline_point_gizmo_id is not None:
                            spline_gizmo_object.visible = True
                            spline_index = list(self.spline_gizmo_object_map).index(self.selected_spline_point_gizmo_id)
                            spline_point = self.selected_object.spline_data.spline_points[spline_index]
                            if spline_gizmo_object_id == self.spline_control_point_gizmo_id0:
                                spline_gizmo_position[...] = spline_point.position - spline_point.control_point
                            elif spline_gizmo_object_id == self.spline_control_point_gizmo_id1:
                                spline_gizmo_position[...] = spline_point.position + spline_point.control_point
                        else:
                            spline_gizmo_object.visible = False
                    else:
                        # spline point gizmo
                        spline_index = list(self.spline_gizmo_object_map).index(spline_gizmo_object_id)
                        spline_point = self.selected_object.spline_data.spline_points[spline_index]
                        spline_gizmo_position[...] = spline_point.position
                    spline_gizmo_object.transform.set_pos(np.dot(Float4(*spline_gizmo_position, 1.0), self.selected_object.transform.matrix)[:3])
                    spline_gizmo_object.update(dt)
                spline_control_point_gizmo_object0 = self.spline_gizmo_object_map.get(self.spline_control_point_gizmo_id0)
                spline_control_point_gizmo_object1 = self.spline_gizmo_object_map.get(self.spline_control_point_gizmo_id1)
                if spline_point_gizmo_object is not None and spline_control_point_gizmo_object0 is not None and spline_control_point_gizmo_object1 is not None:
                    self.renderer.debug_line_manager.draw_debug_line_3d(spline_point_gizmo_object.get_pos(), spline_control_point_gizmo_object0.get_pos(), Float4(0.0, 1.0, 0.0, 1.0), width=3.0)
                    self.renderer.debug_line_manager.draw_debug_line_3d(spline_point_gizmo_object.get_pos(), spline_control_point_gizmo_object1.get_pos(), Float4(0.0, 1.0, 0.0, 1.0), width=3.0)

            # update axis gizmo transform
            spline_control_point_gizmo_object = self.spline_gizmo_object_map.get(self.selected_spline_control_point_gizmo_id)
            axis_gizmo_object = spline_control_point_gizmo_object or spline_point_gizmo_object or self.selected_object
            axis_gizmo_pos = axis_gizmo_object.transform.get_pos()
            self.axis_gizmo.transform.set_pos(axis_gizmo_pos)
            self.axis_gizmo.transform.set_scale(length(axis_gizmo_pos - self.main_camera.transform.get_pos()) * 0.15)
            self.axis_gizmo.update(dt)
