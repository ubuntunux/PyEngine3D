import traceback

import numpy as np
from OpenGL.GL import *

from Core import logger
import Resource


def conversion(value_type, strValue):
    try:
        if value_type == 'Float':
            return np.float32(strValue)
        elif value_type == 'Int':
            return np.int32(strValue)
        elif value_type in ('Vector2', 'Vector3', 'Vector4'):
            vecValue = eval(strValue)
            componentCount = int(value_type[-1])
            if len(vecValue) == componentCount:
                return np.array(vecValue, dtype=np.float32)
            else:
                logger.error(ValueError("%s need %d float numbers." % (value_type, componentCount)))
                raise ValueError
        elif value_type == 'Texture2D':
            return Resource.ResourceManager.instance().getTexture(strValue)
    except ValueError:
        logger.error(traceback.format_exc())
    return None


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
    def bind(self, activateTextureIndex, textureIndex, texture):
        glActiveTexture(activateTextureIndex)
        texture.bind()
        glUniform1i(self.location, textureIndex)
