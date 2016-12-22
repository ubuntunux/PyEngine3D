import os, traceback

import numpy as np
from OpenGL.GL import *

from Utilities import *

NONE_OFFSET = ctypes.c_void_p(0)


# ------------------------------#
# CLASS : Primitive
# ------------------------------#
class Primitive:
    position = np.array([], dtype=np.float32)
    color = np.array([], dtype=np.float32)
    normal = np.array([], dtype=np.float32)
    tangent = np.array([], dtype=np.float32)
    texcoord = np.array([], dtype=np.float32)
    index = np.array([], dtype=np.uint32)

    def __init__(self):
        self.name = ""
        self.position_buffer = -1
        self.color_buffer = -1
        self.normal_buffer = -1
        self.tangent_buffer = -1
        self.texcoord_buffer = -1
        self.index_buffer = -1
        self.vertices = None
        self.attributes = Attributes()

    def initialize(self, primitiveName=""):
        self.name = primitiveName or getClassName(self).lower()

        # position buffer
        self.position_buffer = glGenBuffers(1)  # Request a buffer slot from GPU
        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer)  # Make this buffer the default one
        glBufferData(GL_ARRAY_BUFFER, self.position.nbytes, self.position, GL_STATIC_DRAW)  # Upload data

        # color buffer
        self.color_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.color_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.color.nbytes, self.color, GL_STATIC_DRAW)

        # normal buffer
        self.normal_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.normal_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.normal.nbytes, self.normal, GL_STATIC_DRAW)

        # tangent buffer
        self.tangent_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.tangent_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.tangent.nbytes, self.tangent, GL_STATIC_DRAW)

        # texcoord buffer
        self.texcoord_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.texcoord_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.texcoord.nbytes, self.texcoord, GL_STATIC_DRAW)

        # index buffer
        self.index_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index.nbytes, self.index, GL_STATIC_DRAW)

    def getAttribute(self):
        self.attributes.setAttribute("name", self.name)
        self.attributes.setAttribute("position", len(self.position), type(self.position))
        return self.attributes

    def computeTangent(self):
        if len(self.tangent) == 0:
            self.tangent = np.array([[0, 0, 0], ] * len(self.normal), dtype=np.float32)
            # self.bitangent = np.array([[0,0,0],] * len(self.normal), dtype=np.float32)

            for i in range(0, len(self.index), 3):
                i1, i2, i3 = self.index[i:i + 3]
                deltaPos2 = self.position[i2] - self.position[i1]
                deltaPos3 = self.position[i3] - self.position[i1]
                deltaUV2 = self.texcoord[i2] - self.texcoord[i1]
                deltaUV3 = self.texcoord[i3] - self.texcoord[i1]
                r = (deltaUV2[0] * deltaUV3[1] - deltaUV2[1] * deltaUV3[0])
                r = 1.0 / r if r != 0.0 else 0.0

                tangent = (deltaPos2 * deltaUV3[1] - deltaPos3 * deltaUV2[1]) * r
                tangent = normalize(tangent)
                # bitangent = (deltaPos3 * deltaUV2[0]   - deltaPos2 * deltaUV3[0]) * r
                # bitangent = normalize(bitangent)

                self.tangent[self.index[i]] = tangent
                self.tangent[self.index[i + 1]] = tangent
                self.tangent[self.index[i + 2]] = tangent
                # self.bitangent[self.index[i]] = bitangent
                # self.bitangent[self.index[i+1]] = bitangent
                # self.bitangent[self.index[i+2]] = bitangent

    def bindBuffers(self):
        # Binding buffers
        # loc = glGetAttribLocation(self.shader.program, "position")
        loc = 0
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, self.position.strides[0], NONE_OFFSET)

        # loc = glGetAttribLocation(self.shader.program, "color")
        loc = 1
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.color_buffer)
        glVertexAttribPointer(loc, 4, GL_FLOAT, False, self.color.strides[0], NONE_OFFSET)

        # loc = glGetAttribLocation(self.shader.program, "normal")
        loc = 2
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.normal_buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, self.normal.strides[0], NONE_OFFSET)

        # loc = glGetAttribLocation(self.shader.program, "tangent")
        loc = 3
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.tangent_buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, self.tangent.strides[0], NONE_OFFSET)

        # loc = glGetAttribLocation(self.shader.program, "texcoord")
        loc = 4
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.texcoord_buffer)
        glVertexAttribPointer(loc, 2, GL_FLOAT, False, self.texcoord.strides[0], NONE_OFFSET)

        # bind index buffer
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)

    def draw(self):
        glDrawElements(GL_TRIANGLES, self.index.nbytes, GL_UNSIGNED_INT, NONE_OFFSET)


# ------------------------------#
# CLASS : Mesh
# ------------------------------#
class Mesh(Primitive):
    def __init__(self, meshName, meshData):
        Primitive.__init__(self)
        try:
            # set data
            self.position = np.array(meshData['positions'], dtype=np.float32)
            self.color = np.array(meshData['colors'], dtype=np.float32)
            self.normal = np.array(meshData['normals'], dtype=np.float32)
            self.tangent = np.array(meshData['tangents'], dtype=np.float32)
            self.texcoord = np.array(meshData['texcoords'], dtype=np.float32)
            self.index = np.array(meshData['indices'], dtype=np.uint32)
        except:
            logger.error(traceback.format_exc())
        self.initialize(meshName)


# ------------------------------#
# CLASS : Triangle
# ------------------------------#
class Triangle(Primitive):
    position = np.array([(-1, -1, 0), (1, -1, 0), (-1, 1, 0)], dtype=np.float32)
    color = np.array([(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)], dtype=np.float32)
    normal = np.array([(0, 0, 1), (0, 0, 1), (0, 0, 1)], dtype=np.float32)
    texcoord = np.array([(-1, -1), (1, -1), (-1, 1)], dtype=np.float32)
    index = np.array([0, 1, 2], dtype=np.uint32)

    def __init__(self):
        Primitive.__init__(self)
        self.computeTangent()
        self.initialize()


# ------------------------------#
# CLASS : Quad
# ------------------------------#
class Quad(Primitive):
    position = np.array([(-1, -1, 0), (1, -1, 0), (-1, 1, 0), (1, 1, 0)], dtype=np.float32)
    color = np.array([(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (1, 1, 0, 1)], dtype=np.float32)
    normal = np.array([(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)], dtype=np.float32)
    texcoord = np.array([(-1, -1), (1, -1), (-1, 1), (1, 1)], dtype=np.float32)
    index = np.array([0, 1, 2, 1, 3, 2], dtype=np.uint32)

    def __init__(self):
        Primitive.__init__(self)
        self.computeTangent()
        self.initialize()


# ------------------------------#
# CLASS : DebugLine
# ------------------------------#
class DebugLine:
    def __init__(self, pos1, pos2, width=2.5, color=(1, 1, 0)):
        self.width = width
        self.pos1 = pos1
        self.pos2 = pos2
        self.color = color

    def draw(self):
        glLineWidth(self.width)
        glColor3f(1, 1, 1)
        glBegin(GL_LINES)
        glVertex3f(*self.pos1)
        glVertex3f(*self.pos2)
        glEnd()
