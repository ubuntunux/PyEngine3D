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
        self.set_buffer_data(datas)

    def delete(self):
        glDeleteBuffers(1, [self.buffer, ])

    def set_buffer_data(self, datas):
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)

        size_of_data = sum([data.nbytes for data in datas])
        
        if size_of_data % 16 != 0:
            raise BaseException("Shader storage buffer block must start on a 16-byte padding.")
        
        if 0 < size_of_data:
            glBufferData(GL_SHADER_STORAGE_BUFFER, size_of_data, None, GL_DYNAMIC_COPY)

            offset = 0
            for data in datas:
                glBufferSubData(GL_SHADER_STORAGE_BUFFER, offset, data.nbytes, data)
                offset += data.nbytes

    def bind_storage_buffer(self):
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, self.binding, self.buffer)

    def get_map_buffer(self, inout_data):
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        data_string = string_at(glMapBuffer(GL_SHADER_STORAGE_BUFFER, GL_READ_ONLY), inout_data.nbytes)
        inout_data[...] = np.fromstring(data_string, dtype=inout_data.dtype)
