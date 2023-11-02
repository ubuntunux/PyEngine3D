import traceback

import numpy as np
from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager


ignore_uniform_types = ["atomic_bool", "atomic_uint", "atomic_int", "atomic_float"]


def CreateUniformDataFromString(data_type, strValue=None):
    """ return converted data from string or default data """
    if data_type == 'bool':
        return np.bool_(strValue) if strValue else np.bool_(False)
    elif data_type == 'float':
        # return float(strValue) if strValue else 0.0
        return np.float32(strValue) if strValue else np.float32(0)
    elif data_type == 'int':
        # return int(strValue) if strValue else 0
        return np.int32(strValue) if strValue else np.int32(0)
    elif data_type == 'uint':
        # return int(strValue) if strValue else 0
        return np.uint32(strValue) if strValue else np.uint32(0)
    elif data_type in ('vec2', 'vec3', 'vec4', 'bvec2', 'bvec3', 'bvec4', 'ivec2', 'ivec3', 'ivec4', 'uvec2', 'uvec3', 'uvec4'):
        if data_type in ('bvec2', 'bvec3', 'bvec4', 'ivec2', 'ivec3', 'ivec4'):
            dtype = np.int32
        elif data_type in ('uvec2', 'uvec3', 'uvec4'):
            dtype = np.uint32
        else:
            dtype = np.float32

        componentCount = int(data_type[-1])
        if strValue is not None:
            vecValue = eval(strValue) if type(strValue) is str else strValue
            if len(vecValue) == componentCount:
                return np.array(vecValue, dtype=dtype)
            else:
                logger.error(ValueError("%s need %d float members." % (data_type, componentCount)))
                raise ValueError
        else:
            return np.array([1, ] * componentCount, dtype=dtype)
    elif data_type in ('mat2', 'mat3', 'mat4', 'dmat2', 'dmat3', 'dmat4'):
        if data_type in ('dmat2', 'dmat3', 'dmat4'):
            dtype = np.float32
        else:
            dtype = np.double
        componentCount = int(data_type[-1])
        if strValue is not None:
            vecValue = eval(strValue) if type(strValue) is str else strValue
            if len(vecValue) == componentCount:
                return np.array(vecValue, dtype=dtype)
            else:
                logger.error(ValueError("%s need %d float members." % (data_type, componentCount)))
                raise ValueError
        else:
            return np.eye(componentCount, dtype=dtype)
    elif data_type in ('sampler2D', 'image2D'):
        texture = CoreManager.instance().resource_manager.get_texture(strValue or 'common.flat_white')
        return texture
    elif data_type == 'sampler2DMS':
        logger.warn('sampler2DMS need multisample texture.')
        return CoreManager.instance().resource_manager.get_texture(strValue or 'common.flat_white')
    elif data_type == 'sampler2DArray':
        return CoreManager.instance().resource_manager.get_texture(strValue or 'common.default_2d_array')
    elif data_type in ('sampler3D', 'image3D'):
        return CoreManager.instance().resource_manager.get_texture(strValue or 'common.default_3d')
    elif data_type == 'samplerCube':
        texture = CoreManager.instance().resource_manager.get_texture(strValue or 'common.default_cube')
        return texture

    error_message = 'Cannot find uniform data of %s.' % data_type
    logger.error(error_message)
    raise ValueError(error_message)
    return None


def CreateUniformBuffer(program, uniform_type, uniform_name, default_data=None):
    """ create uniform buffer from .mat(shader) file """
    uniform_classes = [
        UniformBool, UniformInt, UniformUint, UniformFloat,
        UniformVector2, UniformVector3, UniformVector4,
        UniformBoolVector2, UniformBoolVector3, UniformBoolVector4,
        UniformIntVector2, UniformIntVector3, UniformIntVector4,
        UniformUintVector2, UniformUintVector3, UniformUintVector4,
        UniformMatrix2, UniformMatrix3, UniformMatrix4,
        UniformDoubleMatrix2, UniformDoubleMatrix3, UniformDoubleMatrix4,
        UniformTexture2D, UniformTexture2DMultiSample, UniformTexture2DArray, UniformTexture3D, UniformTextureCube,
        UniformImage2D, UniformImage3D
    ]

    for uniform_class in uniform_classes:
        if uniform_type == uniform_class.uniform_type:
            if default_data is not None:
                uniform_data = default_data
            else:
                uniform_data = CreateUniformDataFromString(uniform_type)
            uniform_buffer = uniform_class(program, uniform_name)
            uniform_buffer.set_default_value(uniform_data)
            return uniform_buffer if uniform_buffer.valid else None
    else:
        if uniform_type not in ignore_uniform_types:
            error_message = 'Cannot matched to %s type of %s.' % (uniform_type, uniform_name)
            logger.error(error_message)
            raise BaseException(error_message)
    return None


class UniformVariable:
    data_type = ""
    uniform_type = ""

    def __init__(self, program, variable_name):
        self.name = variable_name
        self.location = glGetUniformLocation(program, variable_name)
        self.show_message = True
        self.default_value = None
        self.valid = True
        if self.location == -1:
            self.valid = False
            # logger.warn("%s location is -1" % variable_name)

    def set_default_value(self, value):
        self.default_value = value

    def get_default_value(self):
        return self.default_value

    def bind_uniform(self, value):
        raise BaseException("You must implement bind function.")


class UniformArray(UniformVariable):
    """future work : http://pyopengl.sourceforge.net/context/tutorials/shader_7.html"""
    uniform_type = ""


class UniformBool(UniformVariable):
    uniform_type = "bool"

    def bind_uniform(self, value):
        glUniform1i(self.location, value)


class UniformInt(UniformVariable):
    uniform_type = "int"

    def bind_uniform(self, value):
        glUniform1i(self.location, value)


class UniformUint(UniformVariable):
    uniform_type = "uint"

    def bind_uniform(self, value):
        glUniform1ui(self.location, value)


class UniformFloat(UniformVariable):
    uniform_type = "float"

    def bind_uniform(self, value):
        glUniform1f(self.location, value)


class UniformVector2(UniformVariable):
    uniform_type = "vec2"

    def bind_uniform(self, value, num=1):
        glUniform2fv(self.location, num, value)


class UniformVector3(UniformVariable):
    uniform_type = "vec3"

    def bind_uniform(self, value, num=1):
        glUniform3fv(self.location, num, value)


class UniformVector4(UniformVariable):
    uniform_type = "vec4"

    def bind_uniform(self, value, num=1):
        glUniform4fv(self.location, num, value)


class UniformBoolVector2(UniformVariable):
    uniform_type = "bvec2"

    def bind_uniform(self, value, num=1):
        glUniform2iv(self.location, num, value)


class UniformBoolVector3(UniformVariable):
    uniform_type = "bvec3"

    def bind_uniform(self, value, num=1):
        glUniform3iv(self.location, num, value)


class UniformBoolVector4(UniformVariable):
    uniform_type = "bvec4"

    def bind_uniform(self, value, num=1):
        glUniform4iv(self.location, num, value)


class UniformIntVector2(UniformVariable):
    uniform_type = "ivec2"

    def bind_uniform(self, value, num=1):
        glUniform2iv(self.location, num, value)


class UniformIntVector3(UniformVariable):
    uniform_type = "ivec3"

    def bind_uniform(self, value, num=1):
        glUniform3iv(self.location, num, value)


class UniformIntVector4(UniformVariable):
    uniform_type = "ivec4"

    def bind_uniform(self, value, num=1):
        glUniform4iv(self.location, num, value)


class UniformUintVector2(UniformVariable):
    uniform_type = "uvec2"

    def bind_uniform(self, value, num=1):
        glUniform2uiv(self.location, num, value)


class UniformUintVector3(UniformVariable):
    uniform_type = "uvec3"

    def bind_uniform(self, value, num=1):
        glUniform3uiv(self.location, num, value)


class UniformUintVector4(UniformVariable):
    uniform_type = "uvec4"

    def bind_uniform(self, value, num=1):
        glUniform4uiv(self.location, num, value)


class UniformMatrix2(UniformVariable):
    uniform_type = "mat2"

    def bind_uniform(self, value, num=1, transpose=False):
        glUniformMatrix2fv(self.location, num, GL_TRUE if transpose else GL_FALSE, value)


class UniformMatrix3(UniformVariable):
    uniform_type = "mat3"

    def bind_uniform(self, value, num=1, transpose=False):
        glUniformMatrix3fv(self.location, num, GL_TRUE if transpose else GL_FALSE, value)


class UniformMatrix4(UniformVariable):
    uniform_type = "mat4"

    def bind_uniform(self, value, num=1, transpose=False):
        glUniformMatrix4fv(self.location, num, GL_TRUE if transpose else GL_FALSE, value)


class UniformDoubleMatrix2(UniformVariable):
    uniform_type = "dmat2"

    def bind_uniform(self, value, num=1, transpose=False):
        glUniformMatrix2dv(self.location, num, GL_TRUE if transpose else GL_FALSE, value)


class UniformDoubleMatrix3(UniformVariable):
    uniform_type = "dmat3"

    def bind_uniform(self, value, num=1, transpose=False):
        glUniformMatrix3dv(self.location, num, GL_TRUE if transpose else GL_FALSE, value)


class UniformDoubleMatrix4(UniformVariable):
    uniform_type = "dmat4"

    def bind_uniform(self, value, num=1, transpose=False):
        glUniformMatrix4dv(self.location, num, GL_TRUE if transpose else GL_FALSE, value)


class UniformTextureBase(UniformVariable):
    uniform_type = "UniformTextureBase"
    texture_offset = 0

    def __init__(self, program, variable_name):
        UniformVariable.__init__(self, program, variable_name)
        self.textureIndex = 0

    def set_texture_index(self, textureIndex):
        self.textureIndex = textureIndex + self.texture_offset

    def bind_uniform(self, texture, wrap=None):
        if texture is not None:
            glActiveTexture(GL_TEXTURE0 + self.textureIndex)
            texture.bind_texture(wrap)
            glUniform1i(self.location, self.textureIndex)
        elif self.show_message:
            self.show_message = False
            logger.error("%s %s is None" % (self.name, self.__class__.__name__))


class UniformTexture2D(UniformTextureBase):
    uniform_type = "sampler2D"
    texture_offset = 0


class UniformTexture2DArray(UniformTextureBase):
    uniform_type = "sampler2DArray"
    texture_offset = 16


class UniformTexture2DMultiSample(UniformTextureBase):
    uniform_type = "sampler2DMS"
    texture_offset = 32


class UniformTexture3D(UniformTextureBase):
    uniform_type = "sampler3D"
    texture_offset = 48


class UniformTextureCube(UniformTextureBase):
    uniform_type = "samplerCube"
    texture_offset = 64


class UniformImageBase(UniformTextureBase):
    uniform_type = "UniformImageBase"

    def set_texture_index(self, textureIndex):
        self.textureIndex = textureIndex

    def bind_uniform(self, texture, level=0, access=GL_READ_WRITE):
        if texture is not None:
            texture.bind_image(self.textureIndex, level, access)
        elif self.show_message:
            self.show_message = False
            logger.error("%s %s is None" % (self.name, self.__class__.__name__))


class UniformImage2D(UniformImageBase):
    uniform_type = "image2D"
    texture_offset = 0


class UniformImage3D(UniformImageBase):
    uniform_type = "image3D"
    texture_offset = 48
