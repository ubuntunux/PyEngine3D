import copy
from collections import OrderedDict
import os
import glob
import math
import time as timeModule

import numpy as np

from Common import logger
from Object import Atmosphere, SkeletonActor, StaticActor, Camera, Light, LightProbe, Sky, PostProcess, RenderInfo
from OpenGLContext import UniformBlock
from Utilities import Singleton, GetClassName, Attributes, FLOAT_ZERO, FLOAT4_ZERO, MATRIX4_IDENTITY, Matrix4, Profiler


class SceneManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.resource_manager = None
        self.sceneLoader = None
        self.renderer = None
        self.__current_scene_name = ""

        # Scene Objects
        self.main_camera = None
        self.main_light = None
        self.main_light_probe = None
        self.selected_object = None

        # envirment object
        self.sky = None
        self.atmosphere = None

        self.cameras = []
        self.lights = []
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
        self.sceneLoader = self.resource_manager.sceneLoader
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
        self.lights = []
        self.light_probes = []
        self.static_actors = []
        self.skeleton_actors = []
        self.objectMap = {}

        # delete empty scene
        # resource = self.resource_manager.sceneLoader.getResource(self.__current_scene_name)
        # if resource is not None and not os.path.exists(resource.meta_data.resource_filepath):
        #     self.resource_manager.sceneLoader.delete_resource(self.__current_scene_name)

    def post_open_scene(self):
        self.renderer.resizeScene(clear_rendertarget=True)
        self.core_manager.sendObjectInfo(self.renderer.postprocess)

    def new_scene(self):
        self.clear_scene()

        # add scene objects
        self.main_camera = self.addCamera()
        self.main_light = self.addLight()
        self.main_light_probe = self.addLightProbe()
        self.atmosphere = Atmosphere()
        self.sky = Sky()

        self.set_current_scene_name(self.resource_manager.sceneLoader.get_new_resource_name("new_scene"))

        logger.info("New scene : %s" % self.__current_scene_name)

        scene_data = self.get_save_data()
        self.resource_manager.sceneLoader.create_resource(self.__current_scene_name, scene_data)

        self.post_open_scene()

    def open_scene(self, scene_name, scene_data):
        self.clear_scene()
        self.set_current_scene_name(scene_name)

        logger.info("Open scene : %s" % scene_name)

        camera_datas = scene_data.get('cameras', [])
        for camera_data in camera_datas:
            self.addCamera(**camera_data)
        self.main_camera = self.get_camera(0)

        light_datas = scene_data.get('lights', [])
        for light_data in light_datas:
            self.addLight(**light_data)
        self.main_light = self.get_light(0)

        light_probe_datas = scene_data.get('light_probes', [])
        if light_probe_datas:
            for light_probe_data in light_probe_datas:
                self.addLightProbe(**light_probe_data)
        else:
            self.addLightProbe()
        self.main_light_probe = self.get_light_probe(0)

        self.sky = Sky()

        self.atmosphere = Atmosphere()

        for object_data in scene_data.get('static_actors', []):
            self.addObject(**object_data)

        for object_data in scene_data.get('skeleton_actors', []):
            self.addObject(**object_data)

        self.post_open_scene()

    def save_scene(self):
        if self.__current_scene_name == "":
            self.set_current_scene_name(self.resource_manager.sceneLoader.get_new_resource_name("new_scene"))
        self.resource_manager.sceneLoader.save_resource(self.__current_scene_name)

    def get_save_data(self):
        scene_data = dict(
            cameras=[camera.get_save_data() for camera in self.cameras],
            lights=[light.get_save_data() for light in self.lights],
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
        elif Light == object_type:
            return self.lights
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
            object_list.remove(object)
            self.objectMap.pop(object.name)
            self.update_render_info(object_type)
            self.core_manager.notifyDeleteObject(object.name)
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

    def addLight(self, **light_data):
        light_data['name'] = self.generateObjectName(light_data.get('name', 'light'))
        light_data['model'] = self.resource_manager.getModel('Cube')
        logger.info("add Light : %s" % light_data['name'])
        light = Light(**light_data)
        self.regist_object(light)
        return light

    def addLightProbe(self, **light_probe_data):
        light_probe_data['name'] = self.generateObjectName(light_probe_data.get('name', 'light_probe'))
        light_probe_data['model'] = self.resource_manager.getModel('sphere')
        logger.info("add Light Probe : %s" % light_probe_data['name'])
        light_probe = LightProbe(**light_probe_data)
        self.regist_object(light_probe)
        return light_probe

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
        self.lights = []
        self.static_actors = []
        self.skeleton_actors = []
        self.objectMap = {}

    def clear_actors(self):
        for obj_name in list(self.objectMap.keys()):
            self.deleteObject(obj_name)

    def deleteObject(self, objName):
        obj = self.getObject(objName)
        if obj and obj not in (self.main_camera, self.main_light, self.main_light_probe):
            self.unregist_resource(obj)

    def getObject(self, objName):
        return self.objectMap[objName] if objName in self.objectMap else None

    def getObjectNames(self):
        return self.objectMap.keys()

    def getObjects(self):
        return self.objectMap.values()

    def get_camera(self, index):
        return self.cameras[index] if index < len(self.cameras) else None

    def get_light(self, index):
        return self.lights[index] if index < len(self.lights) else None

    def get_light_probe(self, index):
        return self.light_probes[index] if index < len(self.light_probes) else None

    def get_static_actor(self, index):
        return self.static_actors[index] if index < len(self.static_actors) else None

    def get_skeleton_actor(self, index):
        return self.skeleton_actors[index] if index < len(self.skeleton_actors) else None

    def getObjectAttribute(self, objName, objTypeName):
        if objTypeName == PostProcess.__name__:
            obj = self.renderer.postprocess
        else:
            obj = self.getObject(objName)
        return obj.getAttribute() if obj else None

    def setObjectAttribute(self, objectName, objectTypeName, attributeName, attributeValue, attribute_index):
        if objectTypeName == PostProcess.__name__:
            obj = self.renderer.postprocess
        else:
            obj = self.getObject(objectName)
        obj and obj.setAttribute(attributeName, attributeValue, attribute_index)

    def getSelectedObject(self):
        return self.selected_object

    def setSelectedObject(self, objName):
        selected_object = self.getObject(objName)
        if self.selected_object is not selected_object:
            if self.selected_object:
                self.selected_object.setSelected(False)
            self.selected_object = selected_object
            if selected_object:
                selected_object.setSelected(True)

    def setObjectFocus(self, objName):
        obj = self.getObject(objName)
        if obj and obj != self.main_camera:
            self.main_camera.transform.setPos(obj.transform.pos - self.main_camera.transform.front * 2.0)

    def set_camera_aspect(self, aspect):
        for camera in self.cameras:
            camera.set_aspect(aspect)

    def update_camera_projection_matrix(self):
        for camera in self.cameras:
            camera.update_projection()

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

        for light in self.lights:
            light.update(self.main_camera)

        for static_actor in self.static_actors:
            static_actor.update(dt)

        for skeleton_actor in self.skeleton_actors:
            skeleton_actor.update(dt)

        self.atmosphere.update(self.main_camera, self.main_light)
