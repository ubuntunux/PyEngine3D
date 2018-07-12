import math
from ctypes import c_void_p
import random

import numpy as np
from OpenGL.GL import *

from Common import logger
from Utilities import compute_tangent
from .OpenGLContext import OpenGLContext


def CreateVertexArrayBuffer(geometry_data):
    geometry_name = geometry_data.get('name', 'VertexArrayBuffer')
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
            if (0 != element_data.nbytes % 16) or (0 != element_data.size % 4):
                raise BaseException("The instance data is a 16-byte boundary. "
                                    "For example, since mat4 is 64 bytes, you need to divide it into 4 by 16 bytes.")

            # The instance data is a 16-byte boundary. For example, since mat4 is 64 bytes,
            # you need to divide it into 4 by 16 bytes.
            divide_count = math.ceil(element_data.nbytes / 16)
            self.divide_counts.append(divide_count)
            self.data_element_count.append(element_data.size)
            self.data_element_size.append(element_data.nbytes)
            self.divided_element_count.append(int(element_data.size / divide_count))
            self.divided_element_size.append(int(element_data.nbytes / divide_count))
            self.data_types.append(OpenGLContext.get_gl_dtype(element_data.dtype))
            self.instance_buffer_offset.append(offset)
            offset += element_data.nbytes

        self.instance_buffer = glGenBuffers(1)

    def bind_instance_buffer(self, *instance_datas, divisor=1):
        instance_buffer_size = 0
        for instance_data in instance_datas:
            instance_buffer_size += instance_data.nbytes
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_buffer)
        glBufferData(GL_ARRAY_BUFFER, instance_buffer_size, None, GL_DYNAMIC_DRAW)

        offset = 0
        location = self.location_offset
        for i, instance_data in enumerate(instance_datas):
            glBufferSubData(GL_ARRAY_BUFFER, offset, instance_data.nbytes, instance_data)

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
            offset += instance_data.nbytes
            location += divide_count


class VertexArrayBuffer:
    def __init__(self, name, datas, index_data):
        self.name = name
        self.vertex_data_count = 0
        self.vertex_buffer_size = 0
        self.vertex_buffer_offset = []
        self.data_element_count = []
        self.data_types = []

        for data in datas:
            element = data[0] if hasattr(data, '__len__') and 0 < len(data) else data
            data_element_count = len(element) if hasattr(element, '__len__') else 1
            if data_element_count == 0:
                continue
            self.data_element_count.append(data_element_count)
            self.data_types.append(OpenGLContext.get_gl_dtype(data.dtype))
            self.vertex_buffer_offset.append(c_void_p(self.vertex_buffer_size))
            self.vertex_buffer_size += data.nbytes
        self.vertex_data_count = len(datas)

        # self.vertex_array = glGenVertexArrays(1)
        # glBindVertexArray(self.vertex_array)
        
        self.vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_buffer_size, None, GL_STATIC_DRAW)

        offset = 0
        for data in datas:
            glBufferSubData(GL_ARRAY_BUFFER, offset, data.nbytes, data)
            offset += data.nbytes

        self.index_buffer_size = index_data.nbytes
        self.index_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_size, index_data, GL_STATIC_DRAW)

    def delete(self):
        glDeleteVertexArrays(1, self.vertex_array)
        glDeleteBuffers(1, self.vertex_buffer)
        glDeleteBuffers(1, self.index_buffer)

    def __bind_vertex_buffer(self):
        if OpenGLContext.need_to_bind_vertex_array(self.vertex_buffer):
            glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)

            for location in range(self.vertex_data_count):
                glEnableVertexAttribArray(location)
                glVertexAttribPointer(location,
                                      self.data_element_count[location],
                                      self.data_types[location],
                                      GL_FALSE,
                                      0,
                                      self.vertex_buffer_offset[location])
                # important : divisor reset
                glVertexAttribDivisor(location, 0)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)

    def draw_elements(self):
        self.__bind_vertex_buffer()
        glDrawElements(GL_TRIANGLES, self.index_buffer_size, GL_UNSIGNED_INT, c_void_p(0))

    def draw_elements_instanced(self, count):
        self.__bind_vertex_buffer()
        glDrawElementsInstanced(GL_TRIANGLES, self.index_buffer_size, GL_UNSIGNED_INT, c_void_p(0), count)
