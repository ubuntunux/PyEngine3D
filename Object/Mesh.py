import os
import pprint
import traceback

import numpy as np
from OpenGL.GL import *

from Core import logger
from Material import VertexArrayBuffer
from Utilities import *

NONE_OFFSET = ctypes.c_void_p(0)


# ------------------------------#
# CLASS : Mesh
# ------------------------------#
class Mesh:
    def __init__(self, mesh_name, mesh_data):
        # meta dats
        self.name = mesh_name
        self.fileSize = mesh_data['fileSize'] if 'fileSize' in mesh_data else 0
        self.modifyTime = mesh_data['modifyTime'] if 'modifyTime' in mesh_data else 0
        self.filePath = mesh_data['filePath'] if 'filePath' in mesh_data else 0

        if 'indices' in mesh_data:
            self.indices = np.array(mesh_data['indices'], dtype=np.uint32)
        else:
            logger.error("Create %s %s  error. Has no index data." % (getClassName(self), mesh_name))
            return

        if 'positions' in mesh_data:
            self.positions = np.array(mesh_data['positions'], dtype=np.float32)
        else:
            logger.error("Create %s %s  error. Has no position data." % (getClassName(self), mesh_name))
            return

        logger.info("Create %s : %s" % (getClassName(self), mesh_name))

        vertex_count = len(self.positions)

        if 'colors' in mesh_data and mesh_data['colors']:
            self.colors = np.array(mesh_data['colors'], dtype=np.float32)
        else:
            self.colors = np.array([1.0, 1.0, 1.0, 1.0] * vertex_count, dtype=np.float32).reshape(vertex_count, 4)

        if 'texcoords' in mesh_data and mesh_data['texcoords']:
            self.texcoords = np.array(mesh_data['texcoords'], dtype=np.float32)
        else:
            self.texcoords = np.array([0.0, 0.0] * vertex_count, dtype=np.float32).reshape(vertex_count, 2)

        if 'normals' in mesh_data and mesh_data['normals']:
            self.normals = np.array(mesh_data['normals'], dtype=np.float32)
        else:
            self.normals = np.array([0.0, 0.0, 1.0] * vertex_count, dtype=np.float32).reshape(vertex_count, 3)

        # Important!! : doing this at last.
        if 'tangents' in mesh_data and mesh_data['tangents']:
            self.tangents = np.array(mesh_data['tangents'], dtype=np.float32)
        else:
            self.computeTangent()

        self.vertexBuffer = self.vertexBuffer = VertexArrayBuffer(
            [self.positions, self.colors, self.normals, self.tangents, self.texcoords],
            self.indices, dtype=np.float32)

        self.attributes = Attributes()

    def clearData(self):
        self.positions = None
        self.colors = None
        self.normals = None
        self.tangents = None
        self.texcoords = None
        self.fileSize = None
        self.modifyTime = None
        self.filePath = None

    def getAttribute(self):
        self.attributes.setAttribute("name", self.name)
        self.attributes.setAttribute("vertex", len(self.positions))
        return self.attributes

    def saveToFile(self, savepath):
        savefilepath = os.path.join(savepath, self.name) + ".mesh"
        logger.info("Save %s : %s" % (getClassName(self), savefilepath))

        try:
            f = open(savefilepath, 'w')
            save_data = dict(
                fileSize=self.fileSize,
                filePath=self.filePath,
                modifyTime=self.modifyTime,
                positions=self.positions.tolist(),
                colors=self.colors.tolist(),
                normals=self.normals.tolist(),
                tangents=self.tangents.tolist(),
                texcoords=self.texcoords.tolist(),
                indices=self.indices.tolist())
            pprint.pprint(save_data, f, compact=True)
            f.close()
        except:
            logger.error(traceback.format_exc())
        return savefilepath

    def computeTangent(self):
        self.tangents = np.array([0.0, 0.0, 0.0] * len(self.normals), dtype=np.float32).reshape(len(self.normals), 3)
        # self.binormal = np.array([0.0, 0.0, 0.0] * len(self.normals), dtype=np.float32).reshape(len(self.normals), 3)

        for i in range(0, len(self.indices), 3):
            i1, i2, i3 = self.indices[i:i + 3]
            deltaPos2 = self.positions[i2] - self.positions[i1]
            deltaPos3 = self.positions[i3] - self.positions[i1]
            deltaUV2 = self.texcoords[i2] - self.texcoords[i1]
            deltaUV3 = self.texcoords[i3] - self.texcoords[i1]
            r = (deltaUV2[0] * deltaUV3[1] - deltaUV2[1] * deltaUV3[0])
            r = 1.0 / r if r != 0.0 else 0.0

            tangent = (deltaPos2 * deltaUV3[1] - deltaPos3 * deltaUV2[1]) * r
            tangent = normalize(tangent)
            # binormal = (deltaPos3 * deltaUV2[0]   - deltaPos2 * deltaUV3[0]) * r
            # binormal = normalize(binormal)

            self.tangents[self.indices[i]] = tangent
            self.tangents[self.indices[i + 1]] = tangent
            self.tangents[self.indices[i + 2]] = tangent
            # self.binormal[self.indices[i]] = binormal
            # self.binormal[self.indices[i+1]] = binormal
            # self.binormal[self.indices[i+2]] = binormal

    def bindBuffers(self):
        self.vertexBuffer.bindBuffer()

    def draw(self):
        glDrawElements(GL_TRIANGLES, self.indices.nbytes, GL_UNSIGNED_INT, NONE_OFFSET)


# ------------------------------#
# CLASS : Triangle
# ------------------------------#
class Triangle(Mesh):
    def __init__(self):
        mesh_data = dict(
            positions=[(-1, -1, 0), (1, -1, 0), (-1, 1, 0)],
            colors=[(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)],
            normals=[(0, 0, 1), (0, 0, 1), (0, 0, 1)],
            texcoords=[(0, 0), (1, 0), (0, 1)],
            indices=[0, 1, 2])
        Mesh.__init__(self, getClassName(self).lower(), mesh_data)
        self.saveToFile(".")



# ------------------------------#
# CLASS : Quad
# ------------------------------#
class Quad(Mesh):
    def __init__(self):
        mesh_data = dict(
            positions=[(-1, -1, 0), (1, -1, 0), (-1, 1, 0), (1, 1, 0)],
            colors=[(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (1, 1, 0, 1)],
            normals=[(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)],
            texcoords=[(0, 0), (1, 0), (0, 1), (1, 1)],
            indices=[0, 1, 2, 1, 3, 2])
        Mesh.__init__(self, getClassName(self).lower(), mesh_data)
        self.saveToFile(".")


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
