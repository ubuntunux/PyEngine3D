import numpy as np
from OpenGL.GL import *

from Utilities import *
from Object import TransformObject

# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
#------------------------------#
# CLASS : Primitive
#------------------------------#
class Primitive(TransformObject):
    data = None
    index = None

    def __init__(self, name='', pos=(0,0,0), material=None):
        # init TransformObject
        TransformObject.__init__(self)

        # init variables
        self.name = name
        self.material = material
        self.shader = self.material.shader
        self.buffer = -1
        self.buffer_index = -1

        # init transform
        self.setPos(pos)
        self.updateTransform()

        # initialize
        self.initialize()

    def initialize(self):
        self.bindBuffers()

    def bindBuffers(self):
        self.buffer = glGenBuffers(1) # Request a buffer slot from GPU
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer) # Make this buffer the default one
        glBufferData(GL_ARRAY_BUFFER, self.data.nbytes, self.data, GL_STATIC_DRAW) # Upload data

        # same for index buffer
        self.buffer_index = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.buffer_index)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index.nbytes, self.index, GL_STATIC_DRAW)

    def draw(self, view, perspective):
        # update transform
        self.updateTransform()

        # use program
        glUseProgram(self.shader.program)
        stride = self.data.strides[0]
        offset = ctypes.c_void_p(0)
        loc = glGetAttribLocation(self.shader.program, "position")
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, stride, offset)

        offset = ctypes.c_void_p(self.data.dtype["position"].itemsize)
        loc = glGetAttribLocation(self.shader.program, "color")
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
        glVertexAttribPointer(loc, 4, GL_FLOAT, False, stride, offset)

        loc = glGetUniformLocation(self.shader.program, "model")
        glUniformMatrix4fv(loc, 1, GL_FALSE, self.matrix)

        loc = glGetUniformLocation(self.shader.program, "view")
        glUniformMatrix4fv(loc, 1, GL_FALSE, view)

        loc = glGetUniformLocation(self.shader.program, "perspective")
        glUniformMatrix4fv(loc, 1, GL_FALSE, perspective)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.buffer_index)
        glDrawElements(GL_TRIANGLES, self.index.nbytes, GL_UNSIGNED_INT, ctypes.c_void_p(0))
        glUseProgram(0)


#------------------------------#
# CLASS : DebugLine
#------------------------------#
class DebugLine:
    def __init__(self, pos1, pos2, width=2.5, color=(1,1,0)):
        self.width = width
        self.pos1 = pos1
        self.pos2 = pos2
        self.color = color

    def draw(self):
        glLineWidth(self.width)
        glColor3f(1,1,1)
        glBegin(GL_LINES)
        glVertex3f(*self.pos1)
        glVertex3f(*self.pos2)
        glEnd()

#------------------------------#
# CLASS : Triangle
#------------------------------#
class Triangle(Primitive):
    data = np.zeros(3, [("position", np.float32, 3), ("color", np.float32, 4)] )
    data['position'] = [ (-1,-1,0), (1,-1,0), (-1,1,0)]
    data['color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1) ]
    index = np.array([0,1,2], dtype=np.uint32)

#------------------------------#
# CLASS : Quad
#------------------------------#
class Quad(Primitive):
    data = np.zeros(4, [("position", np.float32, 3), ("color", np.float32, 4)] )
    data['position'] = [ (-1,-1,1), (1,-1,1), (-1,1,1), (1,1,1) ]
    data['color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
    index = np.array([0,1,2,1,3,2], dtype=np.uint32)


#------------------------------#
# CLASS : Cube
#------------------------------#
class Cube(Primitive):
    data = np.zeros(8, [("position", np.float32, 3), ("color", np.float32, 4)])
    data['color']  = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1),
                        (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
    data['position'] = [ (-1,-1,1),
                        (1,-1,1),
                        (1,1,1),
                        (-1,1,1),
                        (-1,-1,-1),
                        (1,-1,-1),
                        (1,1,-1),
                        (-1,1,-1)]
    index = np.array([0,1,2,
                        2,3,0,
                        1,5,6,
                        6,2,1,
                        7,6,5,
                        5,4,7,
                        4,0,3,
                        3,7,4,
                        4,5,1,
                        1,0,4,
                        3,2,6,
                        6,7,3], dtype=np.uint32)