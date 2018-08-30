import math
import ctypes
from ctypes import sizeof, c_float, c_void_p, c_uint, string_at

import numpy as np
from OpenGL.GL import *

from Common import logger


class AtomicCounterBuffer:
    def __init__(self, name, binding, data):
        self.name = name
        self.binding = binding
        self.type_of_data = np.uint32
        self.size_of_data = np.nbytes[self.type_of_data]
        self.buffer = glGenBuffers(1)
        self.bind_atomic_counter_buffer(data)

    def delete(self):
        glDeleteBuffers(1, [self.buffer, ])

    def bind_atomic_counter_buffer(self, data=None):
        glBindBuffer(GL_ATOMIC_COUNTER_BUFFER, self.buffer)
        glBindBufferBase(GL_ATOMIC_COUNTER_BUFFER, self.binding, self.buffer)
        if data is not None:
            glBufferData(GL_ATOMIC_COUNTER_BUFFER, data.nbytes, None, GL_DYNAMIC_COPY)
            glBufferSubData(GL_ATOMIC_COUNTER_BUFFER, 0, data.nbytes, data)
            self.size_of_data = data.nbytes
            self.type_of_data = data.dtype

    def get_map_buffer(self):
        glBindBuffer(GL_ATOMIC_COUNTER_BUFFER, self.buffer)
        data_ptr = glMapBuffer(GL_ATOMIC_COUNTER_BUFFER, GL_READ_ONLY)
        glUnmapBuffer(GL_ATOMIC_COUNTER_BUFFER)
        glBindBuffer(GL_ATOMIC_COUNTER_BUFFER, 0)

        data_string = string_at(data_ptr, self.size_of_data)
        return np.fromstring(data_string, dtype=self.type_of_data)
