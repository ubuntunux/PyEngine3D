from OpenGL.GL import *
from Utilities import Singleton, getLogger
from Primitive import Primitive, Triangle, Quad

logger = getLogger('default')

class ObjectManager(Singleton):
    primitives = []

    def addPrimitive(self, primitive, name = '', pos = (0,0,0)):
        if issubclass(primitive, Primitive):
            obj = primitive(name = name, pos = pos)
            self.primitives.append(obj)
            logger.info("Add primitive :", obj, obj.name)
        else:
            logger.warning("Unknown primitive.", str(primitive))

    def draw(self):
        for obj in self.primitives:
            glLoadIdentity() # reset view
            glTranslatef(*obj.pos)  # on screen space transform
            obj.draw()


