import numpy as np

from OpenGL.GL import *

class Primitive:
    def __init__(self, name='', pos=(0,0,0), material=None):
        self.name = name
        self.pos = np.array(pos)
        self.material = material

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
        
