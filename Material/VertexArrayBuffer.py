import numpy as np
from OpenGL.GL import *


class VertexArrayBuffer:
    def __init__(self, datas, index_data, dtype):
        self.vertex_unitSize = 0
        self.vertex_strides = []
        self.vertex_stride_points = []
        accStridePoint = 0
        for data in datas:
            if dtype != data.dtype:
                raise AttributeError("dtype is not %s." % str(data.dtype))
            stride = len(data[0]) if len(data) > 0 else 0
            self.vertex_strides.append(stride)
            self.vertex_stride_points.append(ctypes.c_void_p(accStridePoint))
            accStridePoint += stride * np.nbytes[data.dtype]
        self.vertex_unitSize = accStridePoint
        self.vertex_stride_range = range(len(self.vertex_strides))

        self.vertex = np.hstack(datas).astype(dtype)
        self.vertex_array = glGenVertexArrays(1)
        self.vertex_buffer = glGenBuffers(1)

        glBindVertexArray(self.vertex_array)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.vertex, GL_STATIC_DRAW)

        self.index_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, GL_STATIC_DRAW)

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDeleteVertexArrays(1, self.vertex_array)
        glDeleteBuffers(1, self.vertex_buffer)
        glDeleteBuffers(1, self.index_buffer)

    def bindBuffer(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)

        for i in self.vertex_stride_range:
            glVertexAttribPointer(i, self.vertex_strides[i], GL_FLOAT, GL_FALSE, self.vertex_unitSize,
                                  self.vertex_stride_points[i])
            glEnableVertexAttribArray(i)

        # bind index buffer
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)

    def unbindBuffer(self):
        for i in self.vertex_stride_range:
            glDisableVertexAttribArray(i)