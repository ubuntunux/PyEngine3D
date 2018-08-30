import math
import ctypes
from ctypes import sizeof, c_float, c_void_p, c_uint, string_at

import numpy as np
from OpenGL.GL import *

from Common import logger


class ShaderStorageBuffer:
    def __init__(self, name, binding, data):
        self.name = name
        self.binding = binding
        self.type_of_data = np.float32
        self.size_of_data = np.nbytes[self.type_of_data]
        self.buffer = glGenBuffers(1)
        self.bind_storage_buffer(data)

    def delete(self):
        glDeleteBuffers(1, [self.buffer, ])

    def bind_storage_buffer(self, data=None):
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, self.binding, self.buffer)

        if data is not None:
            size_of_data = data.nbytes

            if size_of_data % 16 != 0:
                raise BaseException("Shader storage buffer block must start on a 16-byte padding.")

            if 0 < size_of_data:
                glBufferData(GL_SHADER_STORAGE_BUFFER, size_of_data, None, GL_DYNAMIC_COPY)
                glBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, size_of_data, data)

                self.type_of_data = data.dtype
                self.size_of_data = size_of_data

                # multiple sub data
                # offset = 0
                # for data in datas:
                #     glBufferSubData(GL_SHADER_STORAGE_BUFFER, offset, data.nbytes, data)
                #     offset += data.nbytes

    def get_buffer_data(self):
        # too slow..
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        data_ptr = glMapBuffer(GL_SHADER_STORAGE_BUFFER, GL_READ_ONLY)
        glUnmapBuffer(GL_SHADER_STORAGE_BUFFER)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, 0)

        data_string = string_at(data_ptr, self.size_of_data)
        return np.fromstring(data_string, dtype=self.type_of_data)
