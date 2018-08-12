from ctypes import c_void_p

import numpy as np
from OpenGL.GL import *

from Common import logger


class UniformBlock:
    def __init__(self, buffer_name, program, binding):
        self.name = buffer_name
        self.program = program

        self.buffer_bind = binding
        self.buffer_index = glGetUniformBlockIndex(program, buffer_name)
        glUniformBlockBinding(program, self.buffer_index, binding)

        self.buffer = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)
        # glBufferData(GL_UNIFORM_BUFFER, data.nbytes, data, GL_DYNAMIC_DRAW)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.buffer_bind, self.buffer)

    def delete(self):
        glDeleteBuffers(1, self.buffer)

    def bind_uniform_block(self, data):
        if data.nbytes % 16 != 0:
            raise BaseException("Uniform buffer data must start on a 16-byte padding.")

        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)
        glBufferData(GL_UNIFORM_BUFFER, data.nbytes, data, GL_DYNAMIC_DRAW)
