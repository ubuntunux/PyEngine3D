# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
import traceback

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader, glDeleteShader

from Resource import *
from Core import logger
from Utilities import Singleton, getClassName, Attributes


GLSL_SHADER_VERSION = """#version 430 core\n"""

SCENE_CONSTANTS = """
layout(std140) uniform sceneConstants
{
    mat4 view;
    mat4 perspective;
    vec4 cameraPosition;
    vec4 lightPosition;
    vec4 lightColor;
};
"""


# ------------------------------
# CLASS : VertexArrayBuffer
# ------------------------------
class VertexArrayBuffer:
    def __init__(self, *datas, dtype):
        self.vertex_unitSize = 0
        self.vertex_strides = []
        self.vertex_stride_points = []
        accStridePoint = 0
        for data in datas:
            if dtype != data.dtype:
                raise AttributeException("dtype is not %s." % str(data.dtype))
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

    def bindBuffer(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)

        for i in self.vertex_stride_range:
            glVertexAttribPointer(i, self.vertex_strides[i], GL_FLOAT, GL_FALSE, self.vertex_unitSize,
                                  self.vertex_stride_points[i])
            glEnableVertexAttribArray(i)

    def unbindBuffer(self):
        for i in self.vertex_stride_range:
            glDisableVertexAttribArray(i


# ------------------------------
# CLASS : UniformBuffer
# ------------------------------
class UniformBuffer:
    def __init__(self, *datas, dtype):
        """
        self.sceneConstBuffer = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.sceneConstBuffer)
        self.sceneConstBind = 0
        self.sceneConstIndex = glGetUniformBlockIndex(program, 'sceneConstants')
        glUniformBlockBinding(program, self.sceneConstIndex, self.sceneConstBind)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.sceneConstBind, self.sceneConstBuffer)
        """

        self.vertex_unitSize = 0
        self.vertex_strides = []
        self.vertex_stride_points = []
        accStridePoint = 0
        for data in datas:
            if dtype != data.dtype:
                raise AttributeException("dtype is not %s." % str(data.dtype))
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

    def bindBuffer(self):
        """
        # glBindBuffer(GL_UNIFORM_BUFFER, self.sceneConstBuffer)
        # glUniformBlockBinding(program, self.sceneConstIndex, self.sceneConstBind)
        glBufferData(GL_UNIFORM_BUFFER, sceneConstData.nbytes, sceneConstData, GL_STATIC_DRAW)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.sceneConstBind, self.sceneConstBuffer)
        """
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer)

        for i in self.vertex_stride_range:
            glVertexAttribPointer(i, self.vertex_strides[i], GL_FLOAT, GL_FALSE, self.vertex_unitSize,
                                  self.vertex_stride_points[i])
            glEnableVertexAttribArray(i)

    def unbindBuffer(self):
        for i in self.vertex_stride_range:
            glDisableVertexAttribArray(i)


# ------------------------------
# CLASS : Shader
# ------------------------------
class Shader:
    shaderType = None

    def __init__(self, shaderName, shaderSource):
        logger.info("Create " + getClassName(self) + " : " + shaderName)
        self.name = shaderName
        self.source = GLSL_SHADER_VERSION + SCENE_CONSTANTS + shaderSource
        self.shader = glCreateShader(self.shaderType)
        self.attribute = Attributes()

        # Compile shaders
        try:
            glShaderSource(self.shader, self.source)
            glCompileShader(self.shader)
            if glGetShaderiv(self.shader, GL_COMPILE_STATUS) != 1 or True:
                infoLog = glGetShaderInfoLog(self.shader)
                if infoLog:
                    if type(infoLog) == bytes:
                        infoLog = infoLog.decode("utf-8")
                    logger.error("%s shader error!!!\n" % self.name + infoLog)
                else:
                    logger.info("%s shader complete." % self.name)
        except:
            print(traceback.format_exc())

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        return self.attribute

    def delete(self):
        glDeleteShader(self.shader)


class VertexShader(Shader):
    shaderType = GL_VERTEX_SHADER


class FragmentShader(Shader):
    shaderType = GL_FRAGMENT_SHADER