from ctypes import c_void_p

import numpy as np
from OpenGL.GL import *

from Core import logger


class UniformBlock:
    def __init__(self, buffer_name, program, binding, datas):
        """
        :param datas: [np.array, ...] 16 bytes padding
        """
        self.name = buffer_name
        self.program = program
        self.serializedData = np.hstack([data.flat for data in datas])
        self.blockSize = self.serializedData.nbytes

        if self.blockSize % 16 != 0:
            raise BaseException("Uniform buffer block must start on a 16-byte padding.")

        self.buffer_bind = binding
        self.buffer_index = glGetUniformBlockIndex(program, buffer_name)
        glUniformBlockBinding(program, self.buffer_index, binding)

        self.buffer = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)
        glBufferData(GL_UNIFORM_BUFFER, self.blockSize, c_void_p(0), GL_DYNAMIC_DRAW)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.buffer_bind, self.buffer)

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDeleteBuffers(1, self.buffer)

    def bindData(self, *datas):
        # serialize
        index = 0
        for data in datas:
            self.serializedData[index: index+data.size] = data.flat
            index += data.size

        if self.serializedData.nbytes != self.blockSize:
            logger.error("Uniform buffer block must start on a 16-byte padding.")

        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)
        glBufferSubData(GL_UNIFORM_BUFFER, 0, self.blockSize, self.serializedData)
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

