from OpenGL.GL import *

class Primitive:
    def translate(self, x, y, z):
        glLoadIdentity() # reset view
        glTranslatef(x, y, z)  # on screen space transform
        
    def draw(self):
        pass
    
class Triangle(Primitive):
    def draw(self):
        '''draw triangle'''
        glBegin(GL_POLYGON)
        glVertex3f(-1.0, -1.0, 0.0)
        glVertex3f(1.0, -1.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)
        
        
        glEnd()

class Square(Primitive):
    def draw(self):
        '''draw square'''
        glBegin(GL_QUADS)
        glVertex3f(-1.0, -1.0, 0.0)
        glVertex3f(1.0, -1.0, 0.0)        
        glVertex3f(1.0, 1.0, 0.0)
        glVertex3f(-1.0, 1.0, 0.0)        
        glEnd()