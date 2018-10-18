import math
import ctypes
from ctypes import sizeof, c_float, c_void_p, c_uint, string_at

import numpy as np
from OpenGL.GL import *

from Common import logger


class DispatchIndirectCommand:
    def __init__(self, num_groups_x=1, num_groups_y=1, num_groups_z=1):
        self.data = np.array([num_groups_x, num_groups_y, num_groups_z],
                             dtype=[('num_groups_x', np.uint32),
                                    ('num_groups_y', np.uint32),
                                    ('num_groups_z', np.uint32)])


class DrawElementsIndirectCommand:
    def __init__(self, vertex_count=6, prim_count=1, first_index=0, base_vertex=0, base_instance=0):
        self.data = np.array([vertex_count, prim_count, first_index, base_vertex, base_instance],
                             dtype=[('vertex_count', np.uint32),
                                    ('prim_count', np.uint32),
                                    ('first_index', np.uint32),
                                    ('base_vertex', np.uint32),
                                    ('base_instance', np.uint32)])


class ShaderBuffer:
    target = GL_SHADER_STORAGE_BUFFER
    usage = GL_STATIC_DRAW

    def __init__(self, name, binding, data):
        self.name = name
        self.binding = binding
        self.type_of_data = np.float32
        self.size_of_data = np.nbytes[self.type_of_data]
        self.buffer = glGenBuffers(1)
        self.bind_buffer(data)

    def delete(self):
        glDeleteBuffers(1, [self.buffer, ])

    def bind_buffer(self, data=None):
        glBindBuffer(self.target, self.buffer)
        glBindBufferBase(self.target, self.binding, self.buffer)

        if data is not None:
            self.type_of_data = data.dtype
            self.size_of_data = data.nbytes

            # if self.size_of_data % 16 != 0:
            #     raise BaseException("Shader storage buffer block must start on a 16-byte padding.")

            glBufferData(self.target, self.size_of_data, data, self.usage)

            # multiple sub data
            # offset = 0
            # for data in datas:
            #     glBufferSubData(self.target, offset, data.nbytes, data)
            #     offset += data.nbytes

    def get_buffer_data(self):
        # too slow..
        glBindBuffer(self.target, self.buffer)
        data_ptr = glMapBuffer(self.target, GL_READ_ONLY)
        glUnmapBuffer(self.target)
        glBindBuffer(self.target, 0)

        data_string = string_at(data_ptr, self.size_of_data)
        return np.fromstring(data_string, dtype=self.type_of_data)


class AtomicCounterBuffer(ShaderBuffer):
    target = GL_ATOMIC_COUNTER_BUFFER


class DispatchIndirectBuffer(ShaderBuffer):
    target = GL_DISPATCH_INDIRECT_BUFFER


class DrawElementIndirectBuffer(ShaderBuffer):
    target = GL_DRAW_INDIRECT_BUFFER


class ShaderStorageBuffer(ShaderBuffer):
    target = GL_SHADER_STORAGE_BUFFER
