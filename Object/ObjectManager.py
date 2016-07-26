from collections import OrderedDict
import os, glob

from Resource import ResourceManager
from Core import logger, CoreManager
from Object import BaseObject, Camera, Light
from Render import Renderer
from Utilities import Singleton

#------------------------------#
# CLASS : ObjectManager
#------------------------------#
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

    def initialize(self, renderer):
        logger.info("initialize " + self.__class__.__name__)
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
        name = self.generateObjectName("Camera")
        camera = Camera(name)
        self.cameras.append(camera)
        self.objectMap[name] = camera
        # send camera name to gui
        self.coreManager.sendObjectName(camera)
        return camera

    def addLight(self):
        name = self.generateObjectName("Light")
        # create light
        mesh = self.resourceManager.getMeshByName('Sphere')
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
            material = self.resourceManager.getDefaultMaterial()
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
        return self.objectMap[objName]

    def getObjectList(self):
        return self.objectMap.values()

    def getObjects(self):
        return self.objects

    def getObjectInfos(self, obj):
        info = OrderedDict()
        info['name'] = obj.name
        info['position'] = obj.pos
        info['rotation'] = obj.rot
        info['scale'] = obj.scale
        info['moved'] = False
        return info

    def setObjectData(self, objectName, propertyName, propertyValue):
        obj = self.getObject(objectName)
        if propertyName == 'position':
            obj.setPos(propertyValue)
        elif propertyName == 'rotation':
            obj.setRot(propertyValue)
        elif propertyName == 'scale':
            obj.setScale(propertyValue)

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


