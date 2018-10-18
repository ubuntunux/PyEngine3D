import math
import ctypes
from ctypes import sizeof, c_float, c_void_p, c_uint, string_at

import numpy as np
from OpenGL.GL import *

from Common import logger


def DispatchIndirectCommand(num_groups_x=1, num_groups_y=1, num_groups_z=1):
    return np.array([(num_groups_x, num_groups_y, num_groups_z), ],
                    dtype=[('num_groups_x', np.uint32),
                           ('num_groups_y', np.uint32),
                           ('num_groups_z', np.uint32)])


def DrawElementsIndirectCommand(vertex_count=6, instance_count=1, first_index=0, base_vertex=0, base_instance=0):
    # vertex_count 6 is Quad
    return np.array([(vertex_count, instance_count, first_index, base_vertex, base_instance), ],
                    dtype=[('vertex_count', np.uint32),
                           ('instance_count', np.uint32),
                           ('first_index', np.uint32),
                           ('base_vertex', np.uint32),
                           ('base_instance', np.uint32)])


class ShaderBuffer:
    target = GL_SHADER_STORAGE_BUFFER
    usage = GL_STATIC_DRAW

    def __init__(self, name, binding, data_size, data=None):
        self.name = name
        self.binding = binding
        self.buffer = glGenBuffers(1)
        self.data_size = data_size
        self.set_buffer_data(data)

    def delete(self):
        glDeleteBuffers(1, [self.buffer, ])

    def bind_buffer(self):
        glBindBuffer(self.target, self.buffer)
        glBindBufferBase(self.target, self.binding, self.buffer)

    def set_buffer_data(self, data):
        self.bind_buffer()

        if data is not None and self.data_size != data.nbytes:
            raise BaseException("The data size is different.")

        # if self.data_size % 16 != 0:
        #     raise BaseException("Buffer must be aligned with 16-byte padding.")

        glBufferData(self.target, self.data_size, data, self.usage)

        # multiple sub data
        # offset = 0
        # for data in datas:
        #     glBufferSubData(self.target, offset, data.nbytes, data)
        #     offset += data.nbytes

    def get_buffer_data(self, data_type):
        # too slow..
        glBindBuffer(self.target, self.buffer)
        data_ptr = glMapBuffer(self.target, GL_READ_ONLY)
        glUnmapBuffer(self.target)
        glBindBuffer(self.target, 0)

        data_string = string_at(data_ptr, self.data_size)
        return np.fromstring(data_string, dtype=data_type)


class AtomicCounterBuffer(ShaderBuffer):
    target = GL_ATOMIC_COUNTER_BUFFER


class DispatchIndirectBuffer(ShaderBuffer):
    target = GL_DISPATCH_INDIRECT_BUFFER

    def __init__(self, name, data_size, data):
        super().__init__(name, 0, data_size, data)

    def bind_buffer(self):
        glBindBuffer(self.target, self.buffer)


class DrawElementIndirectBuffer(ShaderBuffer):
    target = GL_DRAW_INDIRECT_BUFFER

    def __init__(self, name, data_size, data):
        super().__init__(name, 0, data_size, data)

    def bind_buffer(self):
        glBindBuffer(self.target, self.buffer)


class ShaderStorageBuffer(ShaderBuffer):
    target = GL_SHADER_STORAGE_BUFFER
