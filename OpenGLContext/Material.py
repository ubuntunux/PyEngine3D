import pickle
import copy
import traceback
from collections import OrderedDict

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader
from OpenGL.arrays import GLbyteArray

import numpy as np

from Common import logger
from Utilities import GetClassName, Attributes, Logger
from .UniformBuffer import CreateUniformBuffer, UniformTextureBase
from App import CoreManager


class Material:
    def __init__(self, material_name, material_datas={}):
        self.valid = False
        logger.info("Load %s material." % material_name)

        vertex_shader_code = material_datas.get('vertex_shader_code', "")
        fragment_shader_code = material_datas.get('fragment_shader_code', "")
        binary_format = material_datas.get('binary_format')
        binary_data = material_datas.get('binary_data')
        uniforms = material_datas.get('uniforms', [])
        self.material_component_names = [x[1] for x in material_datas.get('material_components', [])]
        self.macros = material_datas.get('macros', OrderedDict())

        self.name = material_name
        self.shader_name = material_datas.get('shader_name', '')
        self.program = -1
        self.uniform_buffers = dict()  # OrderedDict()  # Declaration order is important.
        self.Attributes = Attributes()

        if binary_format is not None and binary_data is not None:
            binary_data = np.array(binary_data, dtype=np.ubyte)
            self.compile_from_binary(binary_format, binary_data)
            self.valid = self.check_validate() and self.check_linked()
            if not self.valid:
                logger.error("%s material has been failed to compile from binary" % self.name)
            
        if not self.valid:
            self.compile_from_source(vertex_shader_code, fragment_shader_code)
            self.valid = self.check_validate() and self.check_linked()
            if not self.valid:
                logger.error("%s material has been failed to compile from source" % self.name)

        self.create_uniform_buffers(uniforms)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('shader_name', self.shader_name)
        for key in self.macros:
            self.Attributes.setAttribute(key, self.macros[key])
        return self.Attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if attributeName in self.macros and self.macros[attributeName] != attributeValue:
            new_macros = copy.deepcopy(self.macros)
            new_macros[attributeName] = attributeValue
            # if macro was changed then create a new material.
            CoreManager.instance().resource_manager.getMaterial(self.shader_name, new_macros)

    def delete(self):
        glUseProgram(0)
        glDeleteProgram(self.program)
        logger.info("Deleted %s material." % self.name)

    def use_program(self):
        glUseProgram(self.program)

    def save_to_binary(self):
        size = GLint()
        glGetProgramiv(self.program, GL_PROGRAM_BINARY_LENGTH, size)
        # very important - check data dtype np.ubyte
        binary_data = np.zeros(size.value, dtype=np.ubyte)
        binary_size = GLint()
        binary_format = GLenum()
        glGetProgramBinary(self.program, size.value, binary_size, binary_format, binary_data)
        binary_data = pickle.dumps(binary_data)
        return binary_format, binary_data

    def compile_from_binary(self, binary_format, binary_data):
        binary_data = pickle.loads(binary_data)
        self.program = glCreateProgram()
        glProgramParameteri(self.program, GL_PROGRAM_BINARY_RETRIEVABLE_HINT, GL_TRUE)
        glProgramBinary(self.program, binary_format.value, binary_data, len(binary_data))

    def compile_from_source(self, vertexShaderCode, fragmentShaderCode):
        vertexShader = self.compile(GL_VERTEX_SHADER, vertexShaderCode)
        fragmentShader = self.compile(GL_FRAGMENT_SHADER, fragmentShaderCode)

        if vertexShader is None or fragmentShader is None:
            return False

        self.program = glCreateProgram()
        # glProgramParameteri(self.program, GL_PROGRAM_SEPARABLE, GL_TRUE)
        glProgramParameteri(self.program, GL_PROGRAM_BINARY_RETRIEVABLE_HINT, GL_TRUE)

        glAttachShader(self.program, vertexShader)
        glAttachShader(self.program, fragmentShader)
        glLinkProgram(self.program)

        # delete shader
        glDetachShader(self.program, vertexShader)
        glDetachShader(self.program, fragmentShader)
        glDeleteShader(vertexShader)
        glDeleteShader(fragmentShader)

    def create_uniform_buffers(self, uniforms):
        # create uniform buffers from source code
        active_texture_index = 0
        for uniform_type, uniform_name in uniforms:
            uniform_buffer = CreateUniformBuffer(self.program, uniform_type, uniform_name)
            if uniform_buffer is not None:
                # Important : set texture binding index
                if issubclass(uniform_buffer.__class__, UniformTextureBase):
                    uniform_buffer.set_texture_index(active_texture_index)
                    active_texture_index += 1
                self.uniform_buffers[uniform_name] = uniform_buffer
            else:
                logger.warn("%s material has no %s uniform variable. (or maybe optimized by compiler.)" % (
                    self.name, uniform_name))
        return True

    def compile(self, shaderType, shader_code):
        """
        :param shaderType: GL_VERTEX_SHADER, GL_FRAGMENT_SHADER
        :param shader_code: string
        """
        try:
            # Compile shaders
            shader = glCreateShader(shaderType)
            glShaderSource(shader, shader_code)
            glCompileShader(shader)
            if glGetShaderiv(shader, GL_COMPILE_STATUS) != 1 or True:
                infoLog = glGetShaderInfoLog(shader)
                if infoLog:
                    if type(infoLog) == bytes:
                        infoLog = infoLog.decode("utf-8")
                    logger.error("%s %s shader compile error.\n%s" % (self.name, shaderType.name, infoLog))
                else:
                    # complete
                    logger.log(Logger.MINOR_INFO, "Complete %s %s compile." % (self.name, shaderType.name))
                    return shader
        except:
            logger.error(traceback.format_exc())
        return None

    def check_validate(self):
        glValidateProgram(self.program)
        validation = glGetProgramiv(self.program, GL_VALIDATE_STATUS)
        if validation == GL_FALSE:
            logger.error("Validation failure (%s): %s" % (validation, glGetProgramInfoLog(self.program)))
            return False
        return True

    def check_linked(self):
        link_status = glGetProgramiv(self.program, GL_LINK_STATUS)
        if link_status == GL_FALSE:
            logger.error("Link failure (%s): %s" % (link_status, glGetProgramInfoLog(self.program)))
            return False
        return True
