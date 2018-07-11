import math
import ctypes
from ctypes import sizeof, c_float, c_void_p, c_uint, string_at

import numpy as np
from OpenGL.GL import *

from Common import logger


class ShaderStorageBuffer:
    def __init__(self, name, binding, data):
        self.name = name
        self.buffer = glGenBuffers(1)
        self.binding = binding
        self.data = data  # numpy array

        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        glBufferData(GL_SHADER_STORAGE_BUFFER, self.data.nbytes, self.data, GL_STATIC_DRAW)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, 0)

    def delete(self):
        glDeleteBuffers(1, self.buffer)

    def bind_storage_buffer(self, data=None):
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        if data is not None:
            # new data binding
            self.data = data
            glBufferData(GL_SHADER_STORAGE_BUFFER, self.data.nbytes, self.data, GL_STATIC_DRAW)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, self.binding, self.buffer)

    def map_buffer(self):
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        data_string = string_at(glMapBuffer(GL_SHADER_STORAGE_BUFFER, GL_READ_ONLY), self.data.nbytes)
        self.data[...] = np.fromstring(data_string, dtype=self.data.dtype)
        return self.data
