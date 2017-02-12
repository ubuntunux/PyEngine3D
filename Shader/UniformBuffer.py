import numpy as np
from OpenGL.GL import *

from Core import logger


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

    def bind(self):
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


class UniformColor(UniformVariable):
    def bind(self, color):
        TEST - is need program??
        glUniform4fv(program, self.location, 1, color)


class UniformTexture2D(UniformVariable):
    def bind(self, activateTextureIndex, textureIndex, texture):
        glActiveTexture(activateTextureIndex)
        texture.bind()
        glUniform1i(self.location, textureIndex)
