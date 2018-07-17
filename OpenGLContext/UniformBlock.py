from ctypes import c_void_p

import numpy as np
from OpenGL.GL import *

from Common import logger


class UniformBlock:
    def __init__(self, buffer_name, program, binding, *datas):
        """
        :param datas: [np.array, ...] 16 bytes padding
        """
        self.name = buffer_name
        self.program = program
        self.data = np.zeros(1, dtype=[('', data.dtype, data.shape) for data in datas])
        self.blockSize = self.data.nbytes

        # if self.blockSize % 16 != 0:
        #     raise BaseException("Uniform buffer block must start on a 16-byte padding.")

        self.buffer_bind = binding
        self.buffer_index = glGetUniformBlockIndex(program, buffer_name)
        glUniformBlockBinding(program, self.buffer_index, binding)

        self.buffer = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)
        glBufferData(GL_UNIFORM_BUFFER, self.blockSize, self.data, GL_DYNAMIC_DRAW)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.buffer_bind, self.buffer)

    def delete(self):
        glDeleteBuffers(1, self.buffer)

    def bind_uniform_block(self, *datas):
        for i, data in enumerate(datas):
            self.data[0][i] = data

        if self.data.nbytes != self.blockSize:
            logger.error("Uniform buffer block must start on a 16-byte padding.")

        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)
        glBufferData(GL_UNIFORM_BUFFER, self.blockSize, self.data, GL_DYNAMIC_DRAW)
