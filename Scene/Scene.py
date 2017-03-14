from collections import OrderedDict
import os
import glob
import math
import time as timeModule

from Core import logger, CoreManager
from Material import *
from Object import BaseObject, StaticMesh, Camera, Light
from Resource import ResourceManager
from Render import Renderer, PostProcess
from Utilities import *


class SceneManager(Singleton):
    def __init__(self):
        self.coreManager = None
        self.resourceManager = None
        self.renderer = None

        # Scene Objects
        self.mainCamera = None
        self.cameras = []

        self.lights = []
        self.objects = []
        self.objectMap = {}
        self.selectedObject = None

        self.postprocess = []

        # Test Code : scene constants uniform buffer
        self.uniformSceneConstants = None
        self.uniformLightConstants = None

    def initialize(self):
        logger.info("initialize " + getClassName(self))
        self.coreManager = CoreManager.CoreManager.instance()
        self.resourceManager = ResourceManager.ResourceManager.instance()
        self.renderer = Renderer.Renderer.instance()

        # Test Code : scene constants uniform buffer
        material_instance = self.resourceManager.getMaterialInstance("default")
        self.uniformSceneConstants = UniformBlock("sceneConstants", material_instance.program, 144, 0)
        self.uniformLightConstants = UniformBlock("lightConstants", material_instance.program, 32, 1)

        # add main camera
        self.mainCamera = self.createCamera()

        # default light
        self.createLight()

    def generateObjectName(self, name):
        index = 0
        if name in self.objectMap:
            while True:
                newName = "%s_%d" % (name, index)
                if newName not in self.objectMap:
                    return newName
                index += 1
        return name

    def getMainCamera(self):
        return self.mainCamera

    def createCamera(self):
        name = self.generateObjectName("camera")
        logger.info("Create Camera : %s" % name)
        camera = Camera(name)
        self.cameras.append(camera)
        self.objectMap[name] = camera
        # send camera name to gui
        self.coreManager.sendObjectName(camera)
        return camera

    def createLight(self):
        name = self.generateObjectName("light")
        logger.info("Create Light : %s" % name)
        # create light
        mesh = self.resourceManager.getMesh('sphere')
        material_instance = self.resourceManager.getMaterialInstance('default')
        light = Light(name, (0, 0, 0), mesh, material_instance)

        # add light
        self.lights.append(light)
        self.objectMap[name] = light

        # send light name to gui
        self.coreManager.sendObjectName(light)
        return light

    def createMesh(self, mesh, pos=(0, 0, 0)):
        if mesh:
            # generate name
            objName = self.generateObjectName(mesh.name)
            logger.info("Create Mesh : %s" % objName)

            # create mesh
            material_instance = self.resourceManager.getMaterialInstance("default")
            obj = StaticMesh(objName=objName or mesh.name, pos=pos, mesh=mesh, material_instance=material_instance)

            # add object
            self.objects.append(obj)
            self.objectMap[objName] = obj

            # send object name to ui
            self.coreManager.sendObjectName(obj)
            return obj
        else:
            logger.warning("Unknown mesh : %s" % str(mesh))
        return None

    def createMeshHere(self, mesh):
        camera = self.getMainCamera()
        pos = camera.transform.pos + camera.transform.front * 10.0
        self.createMesh(mesh, pos=pos)

    def clearObjects(self):
        self.objects = []
        self.objectMap = {}

    def getObject(self, objName):
        return self.objectMap[objName] if objName in self.objectMap else None

    def getObjectList(self):
        return self.objectMap.values()

    def getObjects(self):
        return self.objects

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
        obj = self.getObject(objName+"2")
        if obj and obj != self.mainCamera:
            self.mainCamera.transform.setPos(obj.transform.pos - self.mainCamera.transform.front * 2.0)

    def render(self):
        light = self.lights[0]
        light.transform.setPos((math.sin(timeModule.time()) * 10.0, 0.0, math.cos(timeModule.time()) * 10.0))
        viewTransform = self.mainCamera.transform

        # TEST_CODE
        perspective = self.renderer.perspective
        self.uniformSceneConstants.bindData(viewTransform.inverse_matrix.flat,
                                            perspective.flat,
                                            viewTransform.pos, FLOAT_ZERO)
        self.uniformLightConstants.bindData(light.transform.getPos(), FLOAT_ZERO,
                                            light.lightColor)

        # Perspective * View matrix
        vpMatrix = np.dot(viewTransform.inverse_matrix, perspective)

        # draw static meshes
        last_mesh = None
        last_program = None
        last_material_instance = None
        for obj in self.getObjects():
            program = obj.material_instance.program if obj.material_instance else None
            mesh = obj.mesh
            material_instance = obj.material_instance

            if last_program != program:
                glUseProgram(program)
                obj.material_instance.bind()

            if material_instance != last_material_instance:
                material_instance.bind()

            obj.bind(vpMatrix)

            # At last, bind buffers
            if last_mesh != mesh:
                mesh.bindBuffers()

            # draw
            mesh.draw()

            last_program = program
            last_mesh = mesh
            last_material_instance = material_instance

    def update(self):
        for camera in self.cameras:
            camera.update()

        for light in self.lights:
            light.update()

        for obj in self.objects:
            obj.update()
