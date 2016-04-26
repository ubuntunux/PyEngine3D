from Core import logger
from Object import Primitive
from Utilities import Singleton

#------------------------------#
# CLASS : ObjectManager
#------------------------------#
class ObjectManager(Singleton):
    def __init__(self):
        self.primitives = []
        self.primitivesMap = {}
        self.callback_addPrimitive = None
        self.coreManager = None

    def initialize(self, coreManager):
        self.coreManager = coreManager
        logger.info("initialize " + self.__class__.__name__)

    # binding callback function
    def bind_addPrimitive(self, func):
        self.callback_addPrimitive = func

    def addPrimitive(self, primitive, name='', pos=(0,0,0), material=None):
        """
        :param primitive: reference Primitive.py ( Triangle, Quad, etc...)
        """
        if issubclass(primitive, Primitive):
            # generate name
            if name == '':
                name = primitive.__name__

            index = 0
            if name in self.primitivesMap:
                while True:
                    newName = "%s_%d" % (name, index)
                    if newName not in self.primitivesMap:
                        name = newName
                        break
                    index += 1
            # log
            logger.info("Add primitive : %s %s %s" % (primitive.__name__, name, pos))

            # create primitive
            if not material:
                material = self.coreManager.materialManager.getDefaultMaterial()
            obj = primitive(name=name or primitive.__name__, pos=pos, material=material)

            # add object
            self.primitives.append(obj)
            self.primitivesMap[name] = obj

            # callback function on success
            if self.callback_addPrimitive:
                self.callback_addPrimitive(obj.name)
            return obj

        else:
            logger.warning("Unknown primitive : %s" % str(primitive))
        return None

    def getObjectList(self):
        return self.primitives