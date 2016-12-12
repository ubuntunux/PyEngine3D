from collections import OrderedDict
import os, glob

from Resource import ResourceManager
from Core import logger, CoreManager
from Object import BaseObject, Camera, Light
from Render import Renderer
from Utilities import Singleton, getClassName


class ObjectManager(Singleton):
    def __init__(self):
        self.cameras = []
        self.lights = []
        self.renderGroup = {}
        self.objects = []
        self.objectMap = {}
        self.selectedObject = None
        self.mainCamera = None
        self.coreManager = None
        self.resourceManager = None
        self.renderer = None

    def initialize(self):
        logger.info("initialize " + getClassName(self))
        self.coreManager = CoreManager.CoreManager.instance()
        self.resourceManager = ResourceManager.ResourceManager.instance()
        self.renderer = Renderer.Renderer.instance()

        # add main camera
        self.mainCamera = self.addCamera()

        # default light
        self.addLight()

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

    def addCamera(self):
        name = self.generateObjectName("camera")
        camera = Camera(name)
        self.cameras.append(camera)
        self.objectMap[name] = camera
        # send camera name to gui
        self.coreManager.sendObjectName(camera)
        return camera

    def addLight(self):
        name = self.generateObjectName("light")
        # create light
        mesh = self.resourceManager.getMesh('sphere')
        material = self.resourceManager.getMaterial('simple')
        light = Light(name, (0,0,0), mesh, material)

        # add light
        self.lights.append(light)
        self.objectMap[name] = light

        # add to render group
        if mesh.name in self.renderGroup:
            self.renderGroup[mesh.name].append(light)
        else:
            self.renderGroup[mesh.name] = [light, ]

        # send light name to gui
        self.coreManager.sendObjectName(light)
        return light

    def addMesh(self, mesh, pos=(0,0,0)):
        if mesh:
            # generate name
            name = self.generateObjectName(mesh.name)
            logger.info("Add mesh : %s %s %s" % (mesh.name, name, pos))

            # create mesh
            material = self.resourceManager.getMaterial("default")
            obj = BaseObject(name=name or mesh.name, pos=pos, mesh=mesh, material=material)

            # add object
            self.objects.append(obj)
            self.objectMap[name] = obj

            # add to render group
            if mesh.name in self.renderGroup:
                self.renderGroup[mesh.name].append(obj)
            else:
                self.renderGroup[mesh.name] = [obj, ]

            # send object name to ui
            self.coreManager.sendObjectName(obj)
            return obj
        else:
            logger.warning("Unknown mesh : %s" % str(mesh))
        return None

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
        if objName in self.objectMap:
            self.mainCamera.setPos(self.getObject(objName).getPos() - self.mainCamera.front * 2.0)


