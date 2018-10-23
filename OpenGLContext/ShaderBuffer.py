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

    def __init__(self, name, data_size, dtype, init_data=None):
        self.name = name
        self.dtype = dtype
        self.data_size = data_size

        self.buffer = glGenBuffers(1)
        glBindBuffer(self.target, self.buffer)
        glBufferData(self.target, self.data_size, init_data, self.usage)

    def delete(self):
        glDeleteBuffers(1, [self.buffer, ])

    def bind_buffer(self):
        glBindBuffer(self.target, self.buffer)

    def bind_buffer_base(self, binding):
        glBindBufferBase(self.target, binding, self.buffer)

    def clear_buffer(self, internal_format=GL_R32UI, format=GL_RED_INTEGER, type=GL_UNSIGNED_INT):
        # 4 bytes aligned.
        clear_value = np.array([0, ], dtype=np.uint32)
        value_ptr = clear_value.ctypes.data_as(ctypes.c_void_p)

        glBindBuffer(self.target, self.buffer)
        glClearBufferData(self.target, internal_format, format, type, value_ptr)

    def copy_buffer(self, src_buffer):
        if src_buffer.data_size != self.data_size:
            raise BaseException("The source and destination buffers must be the same size.")

        glBindBuffer(GL_COPY_READ_BUFFER, src_buffer.buffer)
        glBindBuffer(GL_COPY_WRITE_BUFFER, self.buffer)
        glCopyBufferSubData(GL_COPY_READ_BUFFER, GL_COPY_WRITE_BUFFER, 0, 0, self.data_size)

    def copy_array_buffer(self, src_array_buffer):
        glBindBuffer(GL_ARRAY_BUFFER, src_array_buffer)
        glBindBuffer(GL_COPY_WRITE_BUFFER, self.buffer)
        glCopyBufferSubData(GL_ARRAY_BUFFER, GL_COPY_WRITE_BUFFER, 0, 0, self.data_size)

    def set_buffer_data(self, data):
        glBindBuffer(self.target, self.buffer)
        glBufferData(self.target, self.data_size, data, self.usage)

        # if data is not None:
        #     # if data.nbytes % 16 != 0:
        #     #     raise BaseException("Buffer must be aligned with 16-byte padding.")
        #     glBufferSubData(self.target, 0, data.nbytes, data)

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

        data_string = string_at(data_ptr, self.data_size)
        return np.fromstring(data_string, dtype=self.dtype)


class AtomicCounterBuffer(ShaderBuffer):
    target = GL_ATOMIC_COUNTER_BUFFER


class DispatchIndirectBuffer(ShaderBuffer):
    target = GL_DISPATCH_INDIRECT_BUFFER

    def bind_buffer_base(self, binding):
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, binding, self.buffer)


class DrawElementIndirectBuffer(ShaderBuffer):
    target = GL_DRAW_INDIRECT_BUFFER

    def bind_buffer_base(self, binding):
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, binding, self.buffer)


class ShaderStorageBuffer(ShaderBuffer):
    target = GL_SHADER_STORAGE_BUFFER
