import traceback

import numpy as np
from OpenGL.GL import *

from Core import logger
import Resource


def create_uniform_buffer(uniform_type, program, uniform_name):
    if uniform_type == "float":
        return UniformFloat(program, uniform_name)
    elif uniform_type == "vec2":
        return UniformVector2(program, uniform_name)
    elif uniform_type == "vec3":
        return UniformVector3(program, uniform_name)
    elif uniform_type == "vec4":
        return UniformVector4(program, uniform_name)
    elif uniform_type == "sampler2D":
        return UniformTexture2D(program, uniform_name)
    return None


def get_uniform_data(data_type, strValue):
    try:
        if data_type == 'Float':
            return np.float32(strValue)
        elif data_type == 'Int':
            return np.int32(strValue)
        elif data_type in ('Vector2', 'Vector3', 'Vector4'):
            vecValue = eval(strValue)
            componentCount = int(data_type[-1])
            if len(vecValue) == componentCount:
                return np.array(vecValue, dtype=np.float32)
            else:
                logger.error(ValueError("%s need %d float members." % (data_type, componentCount)))
                raise ValueError
        elif data_type == 'Texture2D':
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
