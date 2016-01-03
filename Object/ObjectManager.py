from Object import Primitive
from Render import MaterialManager
from Utilities import Singleton
from __main__ import logger

#------------------------------#
# CLASS : ObjectManager
#------------------------------#
class ObjectManager(Singleton):
    def __init__(self):
        self.primitives = []
        self.callback_addPrimitive = None

    def initialize(self):
        pass

    # binding callback function
    def bind_addPrimitive(self, func):
        self.callback_addPrimitive = func

    def addPrimitive(self, primitive, objName='', pos=(0, 0, 0), material=None):
        """
        :param primitive: reference Primitive.py ( Triangle, Quad, etc...)
        """
        if issubclass(primitive, Primitive):
            logger.info("Add primitive :", primitive, objName)
            # create material
            if material is None:
                material = MaterialManager.createMaterial()
            # create primitive
            obj = primitive(name=objName or primitive.__name__, pos=pos, material=material)
            self.primitives.append(obj)
            # callback function on success
            if self.callback_addPrimitive:
                self.callback_addPrimitive(obj.name)
        else:
            logger.warning("Unknown primitive.", str(primitive))

    def getObjectList(self):
        return self.primitives

#------------------------------#
# Globals
#------------------------------#
ObjectManager = ObjectManager.instance()