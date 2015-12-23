from OpenGL.GL import *
from Utilities import Vector

class Primitive:
    pos = None
    name = ''

    def __init__(self, name = '', pos = (0,0,0)):
        self.name = name
        self.pos = Vector(*pos)

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
        
