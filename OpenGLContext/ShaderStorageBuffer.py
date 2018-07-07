import math
from ctypes import c_void_p

import numpy as np
from OpenGL.GL import *

from Common import logger


class ShaderStorageBuffer:
    def __init__(self, name):
        self.name = name
        self.buffer = glGenBuffers(1)

    def bind_storage_buffer(self, binding, data):
        component_count = len(data)
        size_of_data = data.nbytes

        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buffer)
        glBufferData(GL_SHADER_STORAGE_BUFFER, size_of_data, 0, GL_STATIC_DRAW)
        mask = GL_MAP_WRITE_BIT | GL_MAP_INVALIDATE_BUFFER_BIT
        glMapBufferRange(GL_SHADER_STORAGE_BUFFER, 0, size_of_data, mask )
        glUnmapBuffer(GL_SHADER_STORAGE_BUFFER)

        # glBindBufferBase(GL_SHADER_STORAGE_BUFFER, binding, self.buffer)