import traceback

import numpy as np
from OpenGL.GL import *

from Core import logger
import Resource


class UniformVariable:
    def __init__(self, program, variable_name):
        self.name = variable_name
        self.location = glGetUniformLocation(program, variable_name)
        if self.location == -1:
            logger.warn("%s location is -1" % variable_name)

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        pass

    def bind(self, value):
        raise BaseException("You must implement bind function.")


class UniformArray(UniformVariable):
    """future work : http://pyopengl.sourceforge.net/context/tutorials/shader_7.html"""
    pass


class UniformInt(UniformVariable):
    def bind(self, value):
        glUniform1i(self.location, 1, value)


class UniformFloat(UniformVariable):
    def bind(self, value):
        glUniform1f(self.location, value)


class UniformVector2(UniformVariable):
    def bind(self, value):
        glUniform2fv(self.location, 1, value)


class UniformVector3(UniformVariable):
    def bind(self, value):
        glUniform3fv(self.location, 1, value)


class UniformVector4(UniformVariable):
    def bind(self, value):
        glUniform4fv(self.location, 1, value)


class UniformTexture2D(UniformVariable):
    def __init__(self, program, variable_name):
        UniformVariable.__init__(self, program, variable_name)
        self.activateTextureIndex = GL_TEXTURE0
        self.textureIndex = 0

    def set_texture_index(self, activateTextureIndex, textureIndex):
        self.activateTextureIndex = activateTextureIndex
        self.textureIndex = textureIndex

    def bind(self, texture):
        glActiveTexture(self.activateTextureIndex)
        texture.bind() # glBindTexture(texture.target, texture.texture_bind)
        glUniform1i(self.location, self.textureIndex)
