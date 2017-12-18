import math
from ctypes import c_void_p
import random

import numpy as np
from OpenGL.GL import *

from Common import logger
from Utilities import compute_tangent


class InstanceBuffer:
    def __init__(self, name, layout_location, element_data):
        self.name = name
        self.layout_location = layout_location

        self.instance_array = glGenVertexArrays(1)
        glBindVertexArray(self.instance_array)

        self.instance_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_buffer)

        # One of the elements of the instance data list
        self.component_count = len(element_data)
        # The instance data is a 16-byte boundary. For example, since mat4 is 64 bytes,
        # you need to divide it into 4 by 16 bytes.
        self.divide_count = math.ceil(element_data.nbytes / 16)
        self.size_of_data = element_data.nbytes

    def bind_instance_buffer(self, instance_data, divisor=1):
        glBindVertexArray(self.instance_array)
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_buffer)
        glBufferData(GL_ARRAY_BUFFER, instance_data, GL_DYNAMIC_DRAW)

        component_count = len(instance_data[0])
        size_of_data = instance_data[0].nbytes

        if self.divide_count == 1:
            glEnableVertexAttribArray(self.layout_location)
            glVertexAttribPointer(self.layout_location, component_count, GL_FLOAT, GL_FALSE, size_of_data, c_void_p(0))
            # divisor == 0, not instancing.
            # divisor > 0, the attribute advances once per divisor instances of the set(s) of vertices being rendered.
            glVertexAttribDivisor(self.layout_location, divisor)
        else:
            for i in range(self.divide_count):
                glEnableVertexAttribArray(self.layout_location + i)
                glVertexAttribPointer(self.layout_location + i, component_count, GL_FLOAT, GL_FALSE, size_of_data,
                                      c_void_p(self.divide_count * component_count * i))
                glVertexAttribDivisor(self.layout_location + i, divisor)


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
        self.name = name
        self.vertex_component_count = []
        self.vertex_buffer_offset = []
        self.vertex_buffer_size = 0

        for data in datas:
            stride = len(data[0]) if len(data) > 0 else 0
            if stride == 0:
                continue
            self.vertex_component_count.append(stride)
            self.vertex_buffer_offset.append(ctypes.c_void_p(self.vertex_buffer_size))
            self.vertex_buffer_size += stride * np.nbytes[dtype]
        self.layout_location_count = range(len(self.vertex_component_count))

        self.vertex_array = glGenVertexArrays(1)
        glBindVertexArray(self.vertex_array)

        # The important thing is np.hstack. It is to serialize the data.
        vertex_datas = np.hstack(datas).astype(dtype)
        self.vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, vertex_datas, GL_STATIC_DRAW)

        self.index_buffer_size = index_data.nbytes
        self.index_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_size, index_data, GL_STATIC_DRAW)

        self.instance_buffer_map = {}  # { layout_location : (instance_array, instance_buffer) }

    def delete(self):
        glDeleteVertexArrays(1, self.vertex_array)
        glDeleteBuffers(1, self.vertex_buffer)
        glDeleteBuffers(1, self.index_buffer)

        for instance_array, instance_buffer in self.instance_buffer_map.values():
            glDeleteVertexArrays(1, instance_array)
            glDeleteBuffers(1, instance_buffer)

    def create_instance_buffer(self, instance_name, layout_location, element_data):
        self.instance_buffer_map[instance_name] = InstanceBuffer(name=instance_name,
                                                                 layout_location=layout_location,
                                                                 element_data=element_data)

    def bind_instance_buffer(self, instance_name, instance_data, divisor=1):
        instance_buffer = self.instance_buffer_map[instance_name]
        instance_buffer.bind_instance_buffer(instance_data, divisor)

    def bind_vertex_buffer(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)

        for layout_location in self.layout_location_count:
            glEnableVertexAttribArray(layout_location)
            glVertexAttribPointer(layout_location, self.vertex_component_count[layout_location], GL_FLOAT, GL_FALSE,
                                  self.vertex_buffer_size, self.vertex_buffer_offset[layout_location])

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)

    def draw_elements(self):
        glDrawElements(GL_TRIANGLES, self.index_buffer_size, GL_UNSIGNED_INT, c_void_p(0))

    def draw_elements_instanced(self, count):
        glDrawElementsInstanced(GL_TRIANGLES, self.index_buffer_size, GL_UNSIGNED_INT, c_void_p(0), count)

        # important : After the object is drawn You need to execute glDisableVertexAttribArray.
        for instance_buffer in self.instance_buffer_map.values():
            glVertexAttribDivisor(instance_buffer.layout_location, 0)
