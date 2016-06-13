import os

import numpy as np
from OpenGL.GL import *

from Utilities import *

# reference - http://www.labri.fr/perso/nrougier/teaching/opengl

NONE_OFFSET = ctypes.c_void_p(0)

#------------------------------#
# CLASS : Primitive
#------------------------------#
class Primitive:
    position = np.array([], dtype=np.float32)
    color    = np.array([], dtype=np.float32)
    normal   = np.array([], dtype=np.float32)
    index = np.array([], dtype=np.uint32)

    def __init__(self):
        self.name = self.__class__.__name__
        self.position_buffer = -1
        self.color_buffer = -1
        self.normal_buffer = -1
        self.index_buffer = -1

        # position buffer
        self.position_buffer = glGenBuffers(1) # Request a buffer slot from GPU
        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer) # Make this buffer the default one
        glBufferData(GL_ARRAY_BUFFER, self.position.nbytes, self.position, GL_STATIC_DRAW) # Upload data

        # color buffer
        self.color_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.color_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.color.nbytes, self.color, GL_STATIC_DRAW)

        # normal buffer
        self.normal_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.normal_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.normal.nbytes, self.normal, GL_STATIC_DRAW)

        # index buffer
        self.index_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index.nbytes, self.index, GL_STATIC_DRAW)

    def bindBuffers(self):
        # Binding buffers
        #loc = glGetAttribLocation(self.shader.program, "position")
        loc = 0
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, self.position.strides[0], NONE_OFFSET)

        #loc = glGetAttribLocation(self.shader.program, "color")
        loc = 1
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.color_buffer)
        glVertexAttribPointer(loc, 4, GL_FLOAT, False, self.color.strides[0], NONE_OFFSET)

        #loc = glGetAttribLocation(self.shader.program, "normal")
        loc = 2
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.normal_buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, self.normal.strides[0], NONE_OFFSET)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)

    def draw(self):
        glDrawElements(GL_TRIANGLES, self.index.nbytes, GL_UNSIGNED_INT, NONE_OFFSET)


#------------------------------#
# CLASS : Mesh
#------------------------------#
class Mesh(Primitive):
    def __init__(self, name, filename):
        if not os.path.exists(filename):
            return None

        # load from mesh
        f = open(filename, 'r')
        datas = eval(f.read())
        f.close()

        # set data
        self.position = np.array(datas['vertices'], dtype=np.float32)
        self.color    = np.array(datas['vertices'], dtype=np.float32)
        self.normal = np.array(datas['normals'], dtype=np.float32)
        self.index = np.array(datas['indices'], dtype=np.uint32)

        # primitive init
        Primitive.__init__(self)

        # reset name
        self.name = name


#------------------------------#
# CLASS : Triangle
#------------------------------#
class Triangle(Primitive):
    position = np.array([(-1,-1,0), (1,-1,0), (-1,1,0)], dtype=np.float32)
    color    = np.array([(1,0,0,1), (0,1,0,1), (0,0,1,1)], dtype=np.float32)
    normal = np.array([(0,0,1), (0,0,1), (0,0,1)], dtype=np.float32)
    index = np.array([0,1,2], dtype=np.uint32)

#------------------------------#
# CLASS : Quad
#------------------------------#
class Quad(Primitive):
    position = np.array([ (-1,-1,1), (1,-1,1), (-1,1,1), (1,1,1) ], dtype=np.float32)
    color    = np.array([ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ], dtype=np.float32)
    normal = np.array([ (0,0,1), (0,0,1), (0,0,1), (0,0,1) ], dtype=np.float32)
    index = np.array([0,1,2,1,3,2], dtype=np.uint32)


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