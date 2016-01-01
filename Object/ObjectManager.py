from OpenGL.GL import *

from Object import Primitive
from Render import MaterialManager
from Utilities import Singleton, getLogger

logger = getLogger('default')

class ObjectManager(Singleton):
    primitives = []

    def addPrimitive(self, primitive, name='', pos=(0,0,0), material=None):
        if issubclass(primitive, Primitive):
            logger.info("Add primitive :", primitive, name)
            # create material
            if material is None:
                material = MaterialManager().createMaterial()
            # create primitive
            obj = primitive(name=name, pos=pos, material=material)
            self.primitives.append(obj)
        else:
            logger.warning("Unknown primitive.", str(primitive))

    def getObjectList(self):
        return self.primitives