from OpenGL.GL import *
from Utilities import Vector

class Primitive:
    _pos = None
    def __init__(self, pos):
        self._pos = Vector(*pos)

    def translate(self, x, y, z):
        self._pos = (x,y,z)
        glLoadIdentity() # reset view
        glTranslatef(x, y, z)  # on screen space transform
        
    def draw(self):
        pass

class Triangle(Primitive):
    """Triangle"""
    def draw(self):
        glBegin(GL_POLYGON)
        glVertex3f(-1.0, -1.0, 0.0)
        glVertex3f(1.0, -1.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)
        glEnd()

class Quad(Primitive):
    """Quad"""
    def draw(self):
        glBegin(GL_QUADS)
        glVertex3f(-1.0, -1.0, 0.0)
        glVertex3f(1.0, -1.0, 0.0)        
        glVertex3f(1.0, 1.0, 0.0)
        glVertex3f(-1.0, 1.0, 0.0)        
        glEnd()
        
