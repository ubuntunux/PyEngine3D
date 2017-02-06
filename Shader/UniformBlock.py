import numpy as np
from OpenGL.GL import *


class UniformBlock:
    def __init__(self, buffer_name, program):
        self.name = buffer_name
        self.program = program
        self.buffer = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)
        self.buffer_bind = 0
        self.buffer_index = glGetUniformBlockIndex(program, buffer_name)
        glUniformBlockBinding(program, self.buffer_index, self.buffer_bind)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.buffer_bind, self.buffer)

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDeleteBuffers(1, self.buffer)

    def bindData(self, *datas):
        # serialize
        serializedData = np.hstack(datas)

        # DEVELOPMENT
        if serializedData.nbytes % 4 != 0:
            raise BaseException("Uniform buffer block must start on a 16-byte boundary.")

        # glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)
        # glUniformBlockBinding(self.program, self.buffer_index, self.buffer_bind)
        glBufferData(GL_UNIFORM_BUFFER, serializedData.nbytes, serializedData, GL_STATIC_DRAW)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.buffer_bind, self.buffer)