from OpenGL.GL import *

from Material import VertexArrayBuffer
from Utilities import *

NONE_OFFSET = ctypes.c_void_p(0)


# ------------------------------#
# CLASS : Primitive
# ------------------------------#
class Primitive:
    def __init__(self, primitiveName=""):
        self.name = primitiveName or getClassName(self).lower()
        self.position = np.array([], dtype=np.float32)
        self.color = np.array([], dtype=np.float32)
        self.normal = np.array([], dtype=np.float32)
        self.tangent = np.array([], dtype=np.float32)
        self.texcoord = np.array([], dtype=np.float32)
        self.index = np.array([], dtype=np.uint32)
        self.vertexBuffer = None
        self.attributes = Attributes()

    def initialize(self):
        self.vertexBuffer = VertexArrayBuffer([self.position, self.color, self.normal, self.tangent, self.texcoord],
                                              self.index, dtype=np.float32)
        """
        # Example of array buffer

        # buffer initialize
        self.position = np.array([[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]], dtype=np.float32)
        self.position_buffer = glGenBuffers(1)  # Request a buffer slot from GPU
        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer)  # Make this buffer the default one
        glBufferData(GL_ARRAY_BUFFER, self.position.nbytes, self.position, GL_STATIC_DRAW)  # Upload data

        # buffer binding - do per every frame
        # loc = glGetAttribLocation(self.shader.program, "position")
        loc = 0
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, self.position.strides[0], NONE_OFFSET)
        """

    def clearData(self):
        self.position = None
        self.color = None
        self.normal = None
        self.tangent = None
        self.texcoord = None

    def getAttribute(self):
        self.attributes.setAttribute("name", self.name)
        self.attributes.setAttribute("vertex", len(self.position))
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
        self.vertexBuffer.bindBuffer()

    def draw(self):
        glDrawElements(GL_TRIANGLES, self.index.nbytes, GL_UNSIGNED_INT, NONE_OFFSET)


# ------------------------------#
# CLASS : Mesh
# ------------------------------#
class Mesh(Primitive):
    def __init__(self, meshName, meshData):
        Primitive.__init__(self, meshName)
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
        self.initialize()


# ------------------------------#
# CLASS : Triangle
# ------------------------------#
class Triangle(Primitive):
    def __init__(self):
        Primitive.__init__(self)
        self.position = np.array([(-1, -1, 0), (1, -1, 0), (-1, 1, 0)], dtype=np.float32)
        self.color = np.array([(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)], dtype=np.float32)
        self.normal = np.array([(0, 0, 1), (0, 0, 1), (0, 0, 1)], dtype=np.float32)
        self.texcoord = np.array([(0, 1), (1, 1), (0, 0)], dtype=np.float32)
        self.index = np.array([0, 1, 2], dtype=np.uint32)
        self.computeTangent()
        self.initialize()


# ------------------------------#
# CLASS : Quad
# ------------------------------#
class Quad(Primitive):
    def __init__(self):
        Primitive.__init__(self)
        self.position = np.array([(-1, -1, 0), (1, -1, 0), (-1, 1, 0), (1, 1, 0)], dtype=np.float32)
        self.color = np.array([(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (1, 1, 0, 1)], dtype=np.float32)
        self.normal = np.array([(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)], dtype=np.float32)
        self.texcoord = np.array([(0, 1), (1, 1), (0, 0), (1, 0)], dtype=np.float32)
        self.index = np.array([0, 1, 2, 1, 3, 2], dtype=np.uint32)
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
