import copy
from collections import OrderedDict
import os
import glob
import math

import numpy as np

from PyEngine3D.Common import logger
from PyEngine3D.Common.Constants import *
from PyEngine3D.Render import CollisionActor, StaticActor, SkeletonActor
from PyEngine3D.Render import Camera, MainLight, PointLight, LightProbe
from PyEngine3D.Render import gather_render_infos, always_pass, view_frustum_culling_geometry, shadow_culling
from PyEngine3D.Render import Atmosphere, Ocean, Terrain
from PyEngine3D.Render import Effect
from PyEngine3D.Render.RenderOptions import RenderOption
from PyEngine3D.Render.RenderTarget import RenderTargets
from PyEngine3D.Utilities import Singleton, GetClassName


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

        # render group
        self.point_light_count = 0

        self.selected_object_render_info = []
        self.static_solid_render_infos = []
        self.static_translucent_render_infos = []
        self.static_shadow_render_infos = []
        self.skeleton_solid_render_infos = []
        self.skeleton_translucent_render_infos = []
        self.skeleton_shadow_render_infos = []

    def initialize(self, core_manager):
        logger.info("initialize " + GetClassName(self))
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.scene_loader = self.resource_manager.scene_loader
        self.renderer = core_manager.renderer
        self.effect_manager = core_manager.effect_manager

    def get_current_scene_name(self):
        return self.__current_scene_name

    def set_current_scene_name(self, scene_name):
        self.__current_scene_name = scene_name
        self.core_manager.set_window_title(scene_name)

    def clear_scene(self):
        self.core_manager.notify_clear_scene()
        self.effect_manager.clear()
        self.main_camera = None
        self.main_light = None
        self.main_light_probe = None
        self.selected_object = None
        self.cameras = []
        self.point_lights = []
        self.light_probes = []
        self.collision_actors = []
        self.static_actors = []
        self.skeleton_actors = []
        self.objectMap = {}

        self.static_solid_render_infos = []
        self.static_translucent_render_infos = []
        self.skeleton_solid_render_infos = []
        self.skeleton_translucent_render_infos = []

        self.renderer.set_debug_texture(None)

    def begin_open_scene(self):
        self.clear_scene()

    def end_open_scene(self):
        self.renderer.reset_renderer()
        self.regist_object(self.renderer.postprocess)

    def new_scene(self):
        self.begin_open_scene()

        # add scene objects
        self.main_camera = self.add_camera()
        self.main_light = self.add_main_light()
        self.main_light_probe = self.add_light_probe()
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
        return None

    def regist_object(self, obj):
        if obj is not None and obj.name not in self.objectMap:
            object_type = type(obj)
            object_list = self.get_object_list(object_type)
            if object_list is not None:
                object_list.append(obj)
            elif object_type is Effect:
                self.effect_manager.add_effect(obj)
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
        atmosphere.initialize()
        self.regist_object(atmosphere)
        return atmosphere

    def add_ocean(self, **object_data):
        object_data['name'] = self.generate_object_name(object_data.get('name', 'ocean'))
        logger.info("add Ocean : %s" % object_data['name'])
        ocean = Ocean(**object_data)
        self.regist_object(ocean)
        return ocean

    def add_terrain(self, **object_data):
        object_data['name'] = self.generate_object_name(object_data.get('name', 'terrain'))
        logger.info("add Terrain : %s" % object_data['name'])
        terrain = Terrain(**object_data)
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
        mesh = self.resource_manager.get_mesh(collision_data.get('mesh'))
        if mesh is not None:
            collision_data['name'] = name
            collision_data['mesh'] = mesh
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
        if obj is not None and obj not in (self.main_camera, self.main_light, self.main_light_probe):
            self.unregist_resource(obj)

    def get_object(self, object_name):
        return self.objectMap[object_name] if object_name in self.objectMap else None

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

    def set_object_attribute(self, object_name, objectTypeName, attribute_name, attribute_value, parent_info,
                             attribute_index):
        obj = self.get_object(object_name)
        obj and obj.set_attribute(attribute_name, attribute_value, parent_info, attribute_index)

    def get_selected_object(self):
        return self.selected_object

    def set_selected_object(self, object_name):
        selected_object = self.get_object(object_name)
        if self.selected_object is not selected_object:
            if self.selected_object and hasattr(self.selected_object, "set_selected"):
                self.selected_object.set_selected(False)
            self.selected_object = selected_object
            if selected_object and hasattr(selected_object, "set_selected"):
                selected_object.set_selected(True)

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

        gather_render_infos(culling_func=view_frustum_culling_geometry,
                            camera=self.main_camera,
                            light=self.main_light,
                            actor_list=self.collision_actors,
                            solid_render_infos=self.static_solid_render_infos,
                            translucent_render_infos=None)

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
        self.renderer.postprocess.update()

        for camera in self.cameras:
            camera.update()

        if self.main_light is not None:
            self.main_light.update(self.main_camera)

        for light in self.point_lights:
            light.update()

        for collision_actor in self.collision_actors:
            collision_actor.update(dt)

        for static_actor in self.static_actors:
            static_actor.update(dt)

        for skeleton_actor in self.skeleton_actors:
            skeleton_actor.update(dt)

        self.atmosphere.update(self.main_light)
        self.ocean.update(dt)

        if self.terrain.is_render_terrain:
            self.terrain.update(dt)

        self.effect_manager.update(dt)

        # culling
        self.update_static_render_info()
        self.update_skeleton_render_info()
        self.update_light_render_infos()

        self.selected_object_render_info = []
        if self.selected_object is not None and type(self.selected_object) in (SkeletonActor, StaticActor):
            gather_render_infos(culling_func=always_pass,
                                camera=self.main_camera,
                                light=self.main_light,
                                actor_list=[self.selected_object, ],
                                solid_render_infos=self.selected_object_render_info,
                                translucent_render_infos=self.selected_object_render_info)
