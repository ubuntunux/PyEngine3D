from collections import OrderedDict
import os
import glob
import math
import time as timeModule

import numpy as np

from . import logger, CoreManager
from Object import BaseObject, StaticMesh, Camera, Light
from OpenGLContext import UniformBlock
from ResourceManager import ResourceManager
from Render import Tonemapping, Renderer
from Utilities import Singleton, GetClassName, Attributes, FLOAT_ZERO, FLOAT4_ZERO, MATRIX4_IDENTITY


class SceneManager(Singleton):
    def __init__(self):
        self.coreManager = None
        self.resourceManager = None
        self.renderer = None
        self.framebuffer = None
        self.current_scene = None

        # Scene Objects
        self.mainCamera = None
        self.selectedObject = None

        self.cameras = []
        self.lights = []
        self.staticmeshes = []
        self.objectMap = {}  # All of objects

        # postprocess
        self.tonemapping = None

        # Test Code : scene constants uniform buffer
        self.uniformSceneConstants = None
        self.uniformLightConstants = None

    def initialize(self):
        logger.info("initialize " + GetClassName(self))
        self.coreManager = CoreManager.CoreManager.instance()
        self.resourceManager = ResourceManager.ResourceManager.instance()
        self.renderer = Renderer.instance()

        # Test Code : scene constants uniform buffer
        material_instance = self.resourceManager.getMaterialInstance("default")
        program = material_instance.get_program()
        self.uniformSceneConstants = UniformBlock("sceneConstants", program, 0,
                                                  [MATRIX4_IDENTITY, MATRIX4_IDENTITY, FLOAT4_ZERO])
        self.uniformLightConstants = UniformBlock("lightConstants", program, 1, [FLOAT4_ZERO, FLOAT4_ZERO])

        # create scene objects ( camera, light, postprocess )
        self.mainCamera = self.createCamera()
        self.createLight()
        self.create_postprocess()

    def new_scene(self):
        pass

    def load_scene(self, scene_data):
        pass

    def save_scene(self):
        pass

    def generateObjectName(self, currName):
        index = 0
        if currName in self.objectMap:
            while True:
                newName = "%s_%d" % (currName, index)
                if newName not in self.objectMap:
                    return newName
                index += 1
        return currName

    def getMainCamera(self):
        return self.mainCamera

    def createCamera(self):
        camera_name = self.generateObjectName("camera")
        logger.info("Create Camera : %s" % camera_name)
        camera = Camera(camera_name)
        camera.initialize()
        # regist
        self.cameras.append(camera)
        self.objectMap[camera_name] = camera
        return camera

    def createLight(self):
        light_name = self.generateObjectName("light")
        logger.info("Create Light : %s" % light_name)
        # create light
        mesh = self.resourceManager.getMesh('sphere')
        material_instance = self.resourceManager.getMaterialInstance('default')
        light = Light(light_name, (0, 0, 0), mesh, material_instance)
        # regist
        self.lights.append(light)
        self.objectMap[light_name] = light
        return light

    def create_postprocess(self):
        self.tonemapping = Tonemapping(name=self.generateObjectName("tonemapping"))

    def createMesh(self, mesh, pos=(0, 0, 0)):
        if mesh:
            objName = self.generateObjectName(mesh.name)
            logger.info("Create Mesh : %s" % objName)
            # create mesh
            material_instance = self.resourceManager.getMaterialInstance("default")
            obj = StaticMesh(objName=objName or mesh.name, pos=pos, mesh=mesh, material_instance=material_instance)
            # regist
            self.staticmeshes.append(obj)
            self.objectMap[objName] = obj
            return obj
        else:
            logger.warning("Unknown mesh : %s" % str(mesh))
        return None

    def createMeshHere(self, mesh):
        camera = self.getMainCamera()
        pos = camera.transform.pos + camera.transform.front * 10.0
        return self.createMesh(mesh, pos=pos)

    def clearObjects(self):
        self.cameras = []
        self.lights = []
        self.staticmeshes = []
        self.objectMap = {}

    def clearStaticMeshes(self):
        for staticmesh in self.staticmeshes:
            if staticmesh.name in self.objectMap:
                self.objectMap.pop(staticmesh.name)
        self.staticmeshes = []

    def deleteObject(self, objName):
        obj = self.getObject(objName)
        if obj:
            self.objectMap.pop(obj.name)
            if obj in self.cameras:
                self.lights.pop(obj)
            if obj in self.lights:
                self.cameras.pop(obj)
            if obj in self.staticmeshes:
                self.staticmeshes.pop(obj)

    def getObject(self, objName):
        return self.objectMap[objName] if objName in self.objectMap else None

    def getObjectNames(self):
        return self.objectMap.keys()

    def getObjects(self):
        return self.objectMap.values()

    def getStaticMeshes(self):
        return self.staticmeshes

    def getObjectAttribute(self, objName):
        obj = self.getObject(objName)
        return obj.getAttribute() if obj else None

    def setObjectAttribute(self, objectName, attributeName, attributeValue):
        obj = self.getObject(objectName)
        obj and obj.setAttribute(attributeName, attributeValue)

    def getSelectedObject(self):
        return self.selectedObject

    def setSelectedObject(self, objName):
        selectedObject = self.getObject(objName)
        if self.selectedObject is not selectedObject:
            if self.selectedObject:
                self.selectedObject.setSelected(False)
            self.selectedObject = selectedObject
            if selectedObject:
                selectedObject.setSelected(True)

    def setObjectFocus(self, objName):
        obj = self.getObject(objName)
        if obj and obj != self.mainCamera:
            self.mainCamera.transform.setPos(obj.transform.pos - self.mainCamera.transform.front * 2.0)

    def update(self):
        for camera in self.cameras:
            camera.update()

        for light in self.lights:
            light.update()

        for obj in self.staticmeshes:
            obj.update()
