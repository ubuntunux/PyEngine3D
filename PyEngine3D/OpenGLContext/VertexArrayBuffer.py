import math
from ctypes import c_void_p
import random

import numpy as np
from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.Common.Constants import *
from PyEngine3D.Utilities import compute_tangent
from .OpenGLContext import OpenGLContext


def CreateVertexArrayBuffer(geometry_data):
    geometry_name = geometry_data.get('name', 'VertexArrayBuffer')
    # logger.info("Load %s geometry." % geometry_name)

    mode = geometry_data.get('mode', GL_TRIANGLES)
    positions = geometry_data.get('positions', [])
    indices = geometry_data.get('indices', [])
    bone_indicies = geometry_data.get('bone_indicies', [])
    bone_weights = geometry_data.get('bone_weights', [])

    vertex_count = len(positions)
    if 0 == vertex_count:
        logger.error("%s geometry has no position data." % geometry_name)
        return None

    if 0 == len(indices):
        logger.error("%s geometry has no index data." % geometry_name)
        return None

    if not isinstance(positions, np.ndarray):
        positions = np.array(positions, dtype=np.float32)

    if not isinstance(indices, np.ndarray):
        indices = np.array(indices, dtype=np.uint32)

    if not isinstance(bone_indicies, np.ndarray):
        bone_indicies = np.array(bone_indicies, dtype=np.float32)

    if not isinstance(bone_weights, np.ndarray):
        bone_weights = np.array(bone_weights, dtype=np.float32)

    colors = geometry_data.get('colors', [[1.0, 1.0, 1.0, 1.0], ] * vertex_count)
    texcoords = geometry_data.get('texcoords', [[0.0, 0.0], ] * vertex_count)
    normals = geometry_data.get('normals', [[1.0, 1.0, 1.0], ] * vertex_count)
    tangents = geometry_data.get('tangents', [])

    if not isinstance(colors, np.ndarray):
        colors = np.array(colors, dtype=np.float32)

    if not isinstance(texcoords, np.ndarray):
        texcoords = np.array(texcoords, dtype=np.float32)

    if not isinstance(normals, np.ndarray):
        normals = np.array(normals, dtype=np.float32)

    if not isinstance(tangents, np.ndarray):
        tangents = np.array(tangents, dtype=np.float32)

    if len(tangents) == 0:
        is_triangle_mode = (GL_TRIANGLES == mode)
        tangents = compute_tangent(is_triangle_mode, positions, texcoords, normals, indices)

    if 0 < len(bone_indicies) and 0 < len(bone_weights):
        vertex_array_buffer = VertexArrayBuffer(geometry_name,
                                                mode,
                                                [positions, colors, normals, tangents, texcoords, bone_indicies, bone_weights],
                                                indices)
    else:
        vertex_array_buffer = VertexArrayBuffer(geometry_name,
                                                mode,
                                                [positions, colors, normals, tangents, texcoords],
                                                indices)
    return vertex_array_buffer


#  Reference : https://learnopengl.com/Advanced-OpenGL/Instancing
class InstanceBuffer:
    def __init__(self, name, location_offset, element_datas):
        self.name = name
        self.location_offset = location_offset
        self.instance_buffer_offset = []
        self.data_element_count = []
        self.data_element_size = []
        self.data_types = []
        self.divided_element_count = []
        self.divided_element_size = []
        self.divide_counts = []

        offset = 0
        for element_data in element_datas:
            data_element_count = element_data.size
            data_element_size = element_data.nbytes
            dtype = OpenGLContext.get_gl_dtype(element_data.dtype)

            if (0 != data_element_size % 16) or (0 != data_element_count % 4):
                raise BaseException("The instance data is a 16-byte boundary. "
                                    "For example, since mat4 is 64 bytes, you need to divide it into 4 by 16 bytes.")

            # The instance data is a 16-byte boundary. For example, since mat4 is 64 bytes,
            # you need to divide it into 4 by 16 bytes.
            divide_count = math.ceil(data_element_size / 16)
            self.divide_counts.append(divide_count)
            self.data_element_count.append(data_element_count)
            self.data_element_size.append(data_element_size)
            self.divided_element_count.append(int(data_element_count / divide_count))
            self.divided_element_size.append(int(data_element_size / divide_count))
            self.data_types.append(dtype)
            self.instance_buffer_offset.append(offset)
            offset += data_element_size

        self.instance_buffer = glGenBuffers(1)

    def bind_instance_buffer(self, datas, divisor=1):
        instance_buffer_size = sum(data.nbytes for data in datas)
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_buffer)
        glBufferData(GL_ARRAY_BUFFER, instance_buffer_size, None, GL_STATIC_DRAW)

        offset = 0
        location = self.location_offset
        for i, data in enumerate(datas):
            glBufferSubData(GL_ARRAY_BUFFER, offset, data.nbytes, data)

            divide_count = self.divide_counts[i]
            for j in range(divide_count):
                glEnableVertexAttribArray(location + j)
                glVertexAttribPointer(location + j,
                                      self.divided_element_count[i],
                                      self.data_types[i],
                                      GL_FALSE,
                                      self.data_element_size[i],
                                      c_void_p(offset + self.divided_element_size[i] * j))
                # divisor == 0, not instancing.
                # divisor > 0, the attribute advances once per divisor instances of the set(s) of
                # vertices being rendered.
                glVertexAttribDivisor(location + j, divisor)
            offset += data.nbytes
            location += divide_count


class VertexArrayBuffer:
    def __init__(self, name, mode, datas, index_data):
        self.name = name
        self.mode = mode
        self.vertex_buffer_offset = []
        self.data_element_count = []
        self.data_element_size = []
        self.data_types = []

        self.vertex_array = glGenVertexArrays(1)
        glBindVertexArray(self.vertex_array)

        # NOTE : Just one array buffer
        vertex_buffer_size = sum([data.nbytes for data in datas])
        self.vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, vertex_buffer_size, None, GL_STATIC_DRAW)

        offset = 0
        for location, data in enumerate(datas):
            element = data[0] if hasattr(data, '__len__') and 0 < len(data) else data
            data_element_count = len(element) if hasattr(element, '__len__') else 1
            data_element_size = element.nbytes
            data_type = OpenGLContext.get_gl_dtype(data.dtype)

            if data_element_count == 0:
                continue

            glBufferSubData(GL_ARRAY_BUFFER, offset, data.nbytes, data)
            glEnableVertexAttribArray(location)
            glVertexAttribPointer(location, data_element_count, data_type, GL_FALSE, data_element_size, c_void_p(offset))
            # This is very important!!! : divisor reset
            glVertexAttribDivisor(location, 0)
            offset += data.nbytes

        self.index_buffer_size = index_data.nbytes
        self.index_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_size, index_data, GL_STATIC_DRAW)

        glBindVertexArray(0)

    def delete(self):
        logger.info("Delete %s geometry." % self.name)
        glDeleteVertexArrays(1, GLuint(self.vertex_array))
        glDeleteBuffers(1, GLuint(self.vertex_buffer))
        glDeleteBuffers(1, GLuint(self.index_buffer))

    def draw_elements(self):
        OpenGLContext.bind_vertex_array(self.vertex_array)
        glDrawElements(self.mode, self.index_buffer_size, GL_UNSIGNED_INT, NULL_POINTER)

    def draw_elements_instanced(self, instance_count, instance_buffer=None, instance_datas=[]):
        OpenGLContext.bind_vertex_array(self.vertex_array)
        if instance_buffer is not None:
            instance_buffer.bind_instance_buffer(datas=instance_datas)
        glDrawElementsInstanced(self.mode, self.index_buffer_size, GL_UNSIGNED_INT, NULL_POINTER, instance_count)

    def draw_elements_indirect(self, offset=0):
        OpenGLContext.bind_vertex_array(self.vertex_array)
        glDrawElementsIndirect(self.mode, GL_UNSIGNED_INT, c_void_p(offset))
