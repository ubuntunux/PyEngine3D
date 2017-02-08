import numpy as np
import ctypes
from OpenGL.GL import *


class UniformBlock:
    def __init__(self, buffer_name, program, blockSize, binding):
        self.name = buffer_name
        self.program = program

        self.buffer_bind = binding
        self.buffer_index = glGetUniformBlockIndex(program, buffer_name)
        glUniformBlockBinding(program, self.buffer_index, binding)

        self.buffer = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)
        glBufferData(GL_UNIFORM_BUFFER, blockSize, ctypes.c_void_p(0), GL_DYNAMIC_DRAW)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.buffer_bind, self.buffer)

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDeleteBuffers(1, self.buffer)

    def bindData(self, *datas):
        # serialize
        serializedData = np.hstack(datas).astype(np.float32)

        # DEVELOPMENT
        if serializedData.nbytes % 4 != 0:
            raise BaseException("Uniform buffer block must start on a 16-byte boundary.")

        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer)
        glBufferSubData(GL_UNIFORM_BUFFER, 0, serializedData.nbytes, serializedData)
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

