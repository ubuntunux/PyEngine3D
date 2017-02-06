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


class UniformColor(UniformVariable):
    def __init__(self, program, variable_name, color=(1.0, 1.0, 1.0, 1.0)):
        UniformVariable.__init__(self, program, variable_name)
        self.color = np.array(color, dtype=np.float32)

    def bind(self):
        glUniform4fv(self.location, 1, self.color)


class UniformTexture2D(UniformVariable):
    def __init__(self, program, variable_name, texture):
        UniformVariable.__init__(self, program, variable_name)
        if texture is None:
            raise AttributeError("Texture is None.")
        self.texture = texture

    def bind(self, activateTextureIndex, textureIndex):
        glActiveTexture(activateTextureIndex)
        self.texture.bind()
        glUniform1i(self.location, textureIndex)
