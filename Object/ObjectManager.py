from collections import OrderedDict

from Core import logger, CoreManager
from Object import Primitive, Camera
from Utilities import Singleton

#------------------------------#
# CLASS : ObjectManager
#------------------------------#
class ObjectManager(Singleton):
    def __init__(self):
        self.cameras = []
        self.staticMeshes = []
        self.objectMap = {}
        self.mainCamera = None
        self.callback_addPrimitive = None
        self.coreManager = None
        self.renderer = None

    def initialize(self, renderer):
        self.coreManager = CoreManager.CoreManager.instance()
        self.renderer = renderer
        logger.info("initialize " + self.__class__.__name__)
        # add main camera
        self.mainCamera = self.addCamera()

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


    def addPrimitive(self, primitive, pos=(0,0,0)):
        if issubclass(primitive, Primitive):
            # generate name
            name = self.generateObjectName(primitive.__name__)
            logger.info("Add primitive : %s %s %s" % (primitive.__name__, name, pos))

            # create primitive
            material = self.renderer.materialManager.getDefaultMaterial()
            obj = primitive(name=name or primitive.__name__, pos=pos, material=material)

            # add static mesh
            self.staticMeshes.append(obj)
            self.objectMap[name] = obj
            # send object name to ui
            self.coreManager.sendObjectName(obj)

            return obj
        else:
            logger.warning("Unknown primitive : %s" % str(primitive))
        return None

    def getObject(self, objName):
        return self.objectMap[objName]

    def getObjectList(self):
        return self.objectMap.values()

    def getStaticMeshes(self):
        return self.staticMeshes

    def getObjectInfos(self, obj):
        info = OrderedDict()
        info['name'] = obj.name
        info['pos'] = obj.pos
        info['rot'] = obj.rot
        return info

    def setObjectData(self, objectName, propertyName, propertyValue):
        obj = self.getObject(objectName)
        if propertyName == 'pos':
            obj.setPos(propertyValue)
        elif propertyName == 'rot':
            obj.setRot(propertyValue)

    def setObjectFocus(self, obj):
        self.mainCamera.setPos(obj.getPos())


