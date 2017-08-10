from ctypes import c_void_p

import numpy as np
from OpenGL.GL import *

from Common import logger
from Utilities import compute_tangent


def CreateVertexArrayBuffer(geometry_data):
    geometry_name = geometry_data.get('name', '')
    logger.info("Load %s geometry." % geometry_name)

    vertex_count = len(geometry_data.get('positions', []))
    if vertex_count == 0:
        logger.error("%s geometry has no position data." % geometry_name)
        return None

    positions = np.array(geometry_data['positions'], dtype=np.float32)

    if 'indices' not in geometry_data:
        logger.error("%s geometry has no index data." % geometry_name)
        return None

    indices = np.array(geometry_data['indices'], dtype=np.uint32)

    bone_indicies = np.array(geometry_data.get('bone_indicies', []), dtype=np.float32)

    bone_weights = np.array(geometry_data.get('bone_weights', []), dtype=np.float32)

    colors = np.array(geometry_data.get('colors', []), dtype=np.float32)
    if len(colors) == 0:
        colors = np.array([[1.0, 1.0, 1.0, 1.0]] * vertex_count, dtype=np.float32)

    texcoords = np.array(geometry_data.get('texcoords', []), dtype=np.float32)
    if len(texcoords) == 0:
        texcoords = np.array([[0.0, 0.0]] * vertex_count, dtype=np.float32)

    normals = np.array(geometry_data.get('normals', []), dtype=np.float32)
    if len(normals) == 0:
        normals = np.array([[0.0, 0.0, 1.0], ] * vertex_count, dtype=np.float32)

    tangents = np.array(geometry_data.get('tangents', []), dtype=np.float32)
    if len(tangents) == 0:
        tangents = compute_tangent(positions, texcoords, normals, indices)
        geometry_data['tangents'] = tangents.tolist()

    if 0 < len(bone_indicies) and 0 < len(bone_weights):
        vertex_array_buffer = VertexArrayBuffer(geometry_name,
                                     [positions, colors, normals, tangents, texcoords, bone_indicies,
                                      bone_weights], indices)
    else:
        vertex_array_buffer = VertexArrayBuffer(geometry_name, [positions, colors, normals, tangents, texcoords],
                                     indices)
    return vertex_array_buffer


class VertexArrayBuffer:
    def __init__(self, name, datas, index_data, dtype=np.float32):
        """
        :param datas: example [positions, colors, normals, tangents, texcoords]
        :param index_data: indicies
        :param dtype: example, numpy.float32,
        """
        self.name = name
        self.vertex_unitSize = 0
        self.vertex_strides = []
        self.vertex_stride_points = []
        accStridePoint = 0
        for data in datas:
            stride = len(data[0]) if len(data) > 0 else 0
            self.vertex_strides.append(stride)
            self.vertex_stride_points.append(ctypes.c_void_p(accStridePoint))
            accStridePoint += stride * np.nbytes[dtype]
        self.vertex_unitSize = accStridePoint
        self.vertex_stride_range = range(len(self.vertex_strides))

        self.vertex_array = glGenVertexArrays(1)
        glBindVertexArray(self.vertex_array)

        self.vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)

        vertex_datas = np.hstack(datas).astype(dtype)
        glBufferData(GL_ARRAY_BUFFER, vertex_datas, GL_STATIC_DRAW)

        self.index_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)

        self.index_buffer_size = index_data.nbytes
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_size, index_data, GL_STATIC_DRAW)

    def delete(self):
        glDeleteVertexArrays(1, self.vertex_array)
        glDeleteBuffers(1, self.vertex_buffer)
        glDeleteBuffers(1, self.index_buffer)

    def bind_vertex_buffer(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)

        for i in self.vertex_stride_range:
            glVertexAttribPointer(i, self.vertex_strides[i], GL_FLOAT, GL_FALSE, self.vertex_unitSize,
                                  self.vertex_stride_points[i])
            glEnableVertexAttribArray(i)

        # bind index buffer
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)

    def unbind_vertex_buffer(self):
        for i in self.vertex_stride_range:
            glDisableVertexAttribArray(i)

    def draw_elements(self):
        glDrawElements(GL_TRIANGLES, self.index_buffer_size, GL_UNSIGNED_INT, c_void_p(0))
