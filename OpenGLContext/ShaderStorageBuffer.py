import math
import ctypes
from ctypes import sizeof, c_float, c_void_p, c_uint, string_at

import numpy as np
from OpenGL.GL import *

from Common import logger


class ShaderStorageBuffer:
    def __init__(self, name, binding, datas):
        self.name = name
        self.binding = binding
        self.buffer = glGenBuffers(1)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        self.set_buffer_data(datas)

    def delete(self):
        glDeleteBuffers(1, self.buffer)

    @staticmethod
    def set_buffer_data(datas):
        size_of_data = sum([data.nbytes for data in datas])
        if 0 < size_of_data:
            glBufferData(GL_SHADER_STORAGE_BUFFER, size_of_data, None, GL_DYNAMIC_DRAW)

            offset = 0
            for data in datas:
                glBufferSubData(GL_SHADER_STORAGE_BUFFER, offset, data.nbytes, data)
                offset += data.nbytes

    def bind_storage_buffer(self, datas=None):
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        if datas is not None:
            self.set_buffer_data(datas)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, self.binding, self.buffer)

    def map_buffer(self):
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        data_string = string_at(glMapBuffer(GL_SHADER_STORAGE_BUFFER, GL_READ_ONLY), self.data.nbytes)
        self.data[...] = np.fromstring(data_string, dtype=self.data.dtype)
        return self.data
