import copy
from collections import OrderedDict
import os
import glob
import math

import numpy as np

from Common import logger
from Object import SkeletonActor, StaticActor, Camera, MainLight, PointLight, LightProbe, PostProcess, RenderInfo
from Object import Atmosphere, Ocean
from Object.RenderOptions import RenderOption
from Object.RenderTarget import RenderTargets
from OpenGLContext import UniformBlock
from Utilities import Singleton, GetClassName, Attributes, FLOAT_ZERO, FLOAT4_ZERO, MATRIX4_IDENTITY, Matrix4, Profiler


class SceneManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.resource_manager = None
        self.scene_loader = None
        self.renderer = None
        self.__current_scene_name = ""

        # Scene Objects
        self.main_camera = None
        self.main_light = None
        self.main_light_probe = None
        self.selected_object = None

        # envirment object
        self.atmosphere = None
        self.ocean = None

        self.cameras = []
        self.point_lights = []
        self.light_probes = []
        self.static_actors = []
        self.skeleton_actors = []
        self.objectMap = {}  # All of objects

        # render group
        self.static_solid_render_infos = []
        self.static_translucent_render_infos = []
        self.skeleton_solid_render_infos = []
        self.skeleton_translucent_render_infos = []

    def initialize(self, core_manager):
        logger.info("initialize " + GetClassName(self))
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.scene_loader = self.resource_manager.scene_loader
        self.renderer = core_manager.renderer

        # new scene
        self.new_scene()

    def get_current_scene_name(self):
        return self.__current_scene_name

    def set_current_scene_name(self, scene_name):
        self.__current_scene_name = scene_name
        self.core_manager.set_window_title(scene_name)

    def clear_scene(self):
        self.core_manager.notifyClearScene()
        self.main_camera = None
        self.main_light = None
        self.main_light_probe = None
        self.cameras = []
        self.point_lights = []
        self.light_probes = []
        self.static_actors = []
        self.skeleton_actors = []
        self.objectMap = {}

        self.static_solid_render_infos = []
        self.static_translucent_render_infos = []
        self.skeleton_solid_render_infos = []
        self.skeleton_translucent_render_infos = []

        # delete empty scene
        # resource = self.resource_manager.scene_loader.getResource(self.__current_scene_name)
        # if resource is not None and not os.path.exists(resource.meta_data.resource_filepath):
        #     self.resource_manager.scene_loader.delete_resource(self.__current_scene_name)

    def post_open_scene(self):
        self.renderer.resizeScene(clear_rendertarget=True)
        self.regist_object(self.renderer.postprocess)

    def new_scene(self):
        self.clear_scene()

        # add scene objects
        self.main_camera = self.addCamera()
        self.main_light = self.addMainLight()
        self.main_light_probe = self.addLightProbe()
        self.atmosphere = self.addAtmosphere()
        self.ocean = self.addOcean()

        self.set_current_scene_name(self.resource_manager.scene_loader.get_new_resource_name("new_scene"))

        logger.info("New scene : %s" % self.__current_scene_name)

        scene_data = self.get_save_data()
        self.resource_manager.scene_loader.create_resource(self.__current_scene_name, scene_data)

        self.post_open_scene()

    def open_scene(self, scene_name, scene_data):
        self.clear_scene()
        self.set_current_scene_name(scene_name)

        logger.info("Open scene : %s" % scene_name)

        camera_datas = scene_data.get('cameras', [])
        for camera_data in camera_datas:
            self.addCamera(**camera_data)
        self.main_camera = self.cameras[0] if 0 < len(self.cameras) else None

        main_light_data = scene_data.get('main_light', None)
        if main_light_data is not None:
            self.main_light = self.addMainLight(**main_light_data)
        else:
            self.main_light = self.addMainLight()

        light_datas = scene_data.get('lights', [])
        for light_data in light_datas:
            self.addLight(**light_data)

        light_probe_datas = scene_data.get('light_probes', [])
        if light_probe_datas:
            for light_probe_data in light_probe_datas:
                self.addLightProbe(**light_probe_data)
        else:
            self.addLightProbe()
        self.main_light_probe = self.light_probes[0] if 0 < len(self.light_probes) else None

        atmosphere_data = scene_data.get('atmosphere', {})
        self.atmosphere = self.addAtmosphere(**atmosphere_data)

        ocean_data = scene_data.get('ocean', {})
        self.ocean = self.addOcean(**ocean_data)

        for object_data in scene_data.get('static_actors', []):
            self.addObject(**object_data)

        for object_data in scene_data.get('skeleton_actors', []):
            self.addObject(**object_data)

        self.post_open_scene()

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
            static_actors=[static_actor.get_save_data() for static_actor in self.static_actors],
            skeleton_actors=[skeleton_actor.get_save_data() for skeleton_actor in self.skeleton_actors],
        )
        return scene_data

    def generateObjectName(self, currName):
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
        elif StaticActor == object_type:
            return self.static_actors
        elif SkeletonActor == object_type:
            return self.skeleton_actors
        return None

    def regist_object(self, object):
        if object and object.name not in self.objectMap:
            object_type = type(object)
            object_list = self.get_object_list(object_type)
            if object_list is not None:
                object_list.append(object)
            self.objectMap[object.name] = object
            self.update_render_info(object_type)
            self.core_manager.sendObjectInfo(object)
        else:
            logger.error("SceneManager::regist_object error. %s" % object.name if object else 'None')

    def unregist_resource(self, object):
        if object and object.name in self.objectMap:
            object_type = type(object)
            object_list = self.get_object_list(object_type)
            if object_list is not None:
                object_list.remove(object)
            self.objectMap.pop(object.name)
            self.update_render_info(object_type)
            self.core_manager.notifyDeleteObject(object.name)

            if hasattr(object, 'delete'):
                object.delete()
        else:
            logger.error("SceneManager::unregist_resource error. %s" % object.name if object else 'None')

    def addCamera(self, **camera_data):
        camera_data['name'] = self.generateObjectName(camera_data.get('name', 'camera'))
        camera_data['model'] = self.resource_manager.getModel('Cube')
        logger.info("add Camera : %s" % camera_data['name'])
        camera = Camera(scene_manager=self, **camera_data)
        camera.initialize()
        self.regist_object(camera)
        return camera

    def addMainLight(self, **light_data):
        light_data['name'] = self.generateObjectName(light_data.get('name', 'main_light'))
        light_data['model'] = self.resource_manager.getModel('Cube')
        logger.info("add MainLight : %s" % light_data['name'])
        light = MainLight(**light_data)
        self.regist_object(light)
        return light

    def addLight(self, **light_data):
        light_data['name'] = self.generateObjectName(light_data.get('name', 'light'))
        light_data['model'] = self.resource_manager.getModel('Cube')
        logger.info("add Light : %s" % light_data['name'])
        light = PointLight(**light_data)
        self.regist_object(light)
        return light

    def addLightProbe(self, **light_probe_data):
        light_probe_data['name'] = self.generateObjectName(light_probe_data.get('name', 'light_probe'))
        light_probe_data['model'] = self.resource_manager.getModel('sphere')
        logger.info("add Light Probe : %s" % light_probe_data['name'])
        light_probe = LightProbe(**light_probe_data)
        self.regist_object(light_probe)
        return light_probe

    def addAtmosphere(self, **atmosphere_data):
        atmosphere_data['name'] = self.generateObjectName(atmosphere_data.get('name', 'atmosphere'))
        logger.info("add Atmosphere : %s" % atmosphere_data['name'])
        atmosphere = Atmosphere(**atmosphere_data)
        self.regist_object(atmosphere)
        return atmosphere

    def addOcean(self, **object_data):
        object_data['name'] = self.generateObjectName(object_data.get('name', 'ocean'))
        logger.info("add Ocean : %s" % object_data['name'])
        ocean = Ocean(**object_data)
        self.regist_object(ocean)
        return ocean

    def addObject(self, **object_data):
        model = object_data.get('model')
        if model:
            object_data['name'] = self.generateObjectName(object_data.get('name', model.name))
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

    def addObjectHere(self, model):
        pos = self.main_camera.transform.pos + self.main_camera.front * 10.0
        return self.addObject(model=model, pos=pos)

    def clearObjects(self):
        self.cameras = []
        self.point_lights = []
        self.static_actors = []
        self.skeleton_actors = []
        self.objectMap = {}

    def clear_actors(self):
        for obj_name in list(self.objectMap.keys()):
            self.deleteObject(obj_name)

    def actionObject(self, objectName):
        obj = self.getObject(objectName)
        if obj is not None:
            object_type = type(obj)
            if LightProbe == object_type:
                self.renderer.set_debug_texture(obj.texture_probe)
                self.core_manager.sendObjectAttribute(obj.texture_probe.getAttribute())

    def deleteObject(self, objectName):
        obj = self.getObject(objectName)
        if obj and obj not in (self.main_camera, self.main_light, self.main_light_probe):
            self.unregist_resource(obj)

    def getObject(self, objectName):
        return self.objectMap[objectName] if objectName in self.objectMap else None

    def getObjectNames(self):
        return self.objectMap.keys()

    def getObjects(self):
        return self.objectMap.values()

    def get_light_probe_texture(self):
        if RenderOption.RENDER_LIGHT_PROBE:
            return RenderTargets.LIGHT_PROBE_ATMOSPHERE
        return self.main_light_probe.texture_probe

    def reset_light_probe(self):
        for light_probe in self.light_probes:
            light_probe.isRendered = False

    def getObjectAttribute(self, objectName, objectTypeName):
        obj = self.getObject(objectName)
        return obj.getAttribute() if obj else None

    def setObjectAttribute(self, objectName, objectTypeName, attributeName, attributeValue, attribute_index):
        obj = self.getObject(objectName)
        obj and obj.setAttribute(attributeName, attributeValue, attribute_index)

    def getSelectedObject(self):
        return self.selected_object

    def setSelectedObject(self, objectName):
        selected_object = self.getObject(objectName)
        if self.selected_object is not selected_object:
            if self.selected_object and hasattr(self.selected_object, "setSelected"):
                self.selected_object.setSelected(False)
            self.selected_object = selected_object
            if selected_object and hasattr(selected_object, "setSelected"):
                selected_object.setSelected(True)

    def setObjectFocus(self, objectName):
        obj = self.getObject(objectName)
        if obj and obj != self.main_camera:
            self.main_camera.transform.setPos(obj.transform.pos - self.main_camera.transform.front * 2.0)

    def update_camera_projection_matrix(self, fov=0.0, aspect=0.0):
        for camera in self.cameras:
            camera.update_projection(fov, aspect)

    def update_render_info(self, object_type):
        if StaticActor == object_type:
            self.update_static_render_info()
        elif SkeletonActor == object_type:
            self.update_skeleton_render_info()

    def update_static_render_info(self):
        self.static_solid_render_infos = []
        self.static_translucent_render_infos = []

        RenderInfo.gather_render_infos(actor_list=self.static_actors,
                                       solid_render_infos=self.static_solid_render_infos,
                                       translucent_render_infos=self.static_translucent_render_infos)

        self.static_solid_render_infos.sort(key=lambda x: (id(x.geometry), id(x.material)))
        self.static_translucent_render_infos.sort(key=lambda x: (id(x.geometry), id(x.material)))

    def update_skeleton_render_info(self):
        self.skeleton_solid_render_infos = []
        self.skeleton_translucent_render_infos = []

        RenderInfo.gather_render_infos(actor_list=self.skeleton_actors,
                                       solid_render_infos=self.skeleton_solid_render_infos,
                                       translucent_render_infos=self.skeleton_translucent_render_infos)

        self.skeleton_solid_render_infos.sort(key=lambda x: (id(x.geometry), id(x.material)))
        self.skeleton_translucent_render_infos.sort(key=lambda x: (id(x.geometry), id(x.material)))

    def update_scene(self, dt):
        self.renderer.postprocess.update()

        for camera in self.cameras:
            camera.update()

        if self.main_light is not None:
            self.main_light.update(self.main_camera)

        for light in self.point_lights:
            light.update()

        for static_actor in self.static_actors:
            static_actor.update(dt)

        for skeleton_actor in self.skeleton_actors:
            skeleton_actor.update(dt)

        self.atmosphere.update(self.main_light)

        self.ocean.update(dt)
