from collections import OrderedDict
import os, glob

from Core import logger, CoreManager
from Object import BaseObject, Camera, Triangle, Quad, Mesh
from Utilities import Singleton

#------------------------------#
# CLASS : ObjectManager
#------------------------------#
class ObjectManager(Singleton):
    def __init__(self):
        self.cameras = []
        self.primitives = {}
        self.renderGroup = {}
        self.objects = []
        self.objectMap = {}
        self.selectedObject = None
        self.mainCamera = None
        self.coreManager = None
        self.renderer = None

    def initialize(self, renderer):
        self.coreManager = CoreManager.CoreManager.instance()
        self.renderer = renderer
        logger.info("initialize " + self.__class__.__name__)

        # add main camera
        self.mainCamera = self.addCamera()

        # regist primitives
        self.registPrimitives()

    def registPrimitives(self):
        self.primitives['Triangle'] = Triangle()
        self.primitives['Quad'] = Quad()
        # regist obj files
        for filename in glob.glob(os.path.join('Resources', 'Meshes', '*.mesh')):
            name = os.path.splitext(os.path.split(filename)[1])[0]
            name = name[0].upper() + name[1:]
            self.primitives[name] = Mesh(name, filename)


    def getPrimitiveNameList(self):
        return list(self.primitives.keys())

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

    def getPrimitiveByName(self, primitiveName):
        return self.primitives[primitiveName] if primitiveName in self.primitives else None

    def addPrimitive(self, primitive, pos=(0,0,0)):
        if primitive:
            # generate name
            name = self.generateObjectName(primitive.name)
            logger.info("Add primitive : %s %s %s" % (primitive.name, name, pos))

            # create primitive
            material = self.renderer.materialManager.getDefaultMaterial()
            obj = BaseObject(name=name or primitive.name, pos=pos, primitive=primitive, material=material)

            # add object
            self.objects.append(obj)
            self.objectMap[name] = obj
            if primitive.name in self.renderGroup:
                self.renderGroup[primitive.name].append(obj)
            else:
                self.renderGroup[primitive.name] = [obj, ]

            # send object name to ui
            self.coreManager.sendObjectName(obj)
            return obj
        else:
            logger.warning("Unknown primitive : %s" % str(primitive))
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


