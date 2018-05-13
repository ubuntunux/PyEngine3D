import re
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

        shader_codes = material_datas.get('shader_codes')
        binary_format = material_datas.get('binary_format')
        binary_data = material_datas.get('binary_data')
        uniforms = material_datas.get('uniforms', [])
        self.material_component_names = [x[1] for x in material_datas.get('material_components', [])]
        self.macros = material_datas.get('macros', OrderedDict())

        self.is_translucent = True if 0 < self.macros.get('TRANSPARENT_MATERIAL', 0) else False

        self.name = material_name
        self.shader_name = material_datas.get('shader_name', '')
        self.program = -1
        self.uniform_buffers = dict()  # OrderedDict()  # Declaration order is important.
        self.Attributes = Attributes()

        if binary_format is not None and binary_data is not None:
            self.compile_from_binary(binary_format, binary_data)
            self.valid = self.check_validate() and self.check_linked()
            if not self.valid:
                logger.error("%s material has been failed to compile from binary" % self.name)

        self.compile_message = ""

        if not self.valid:
            self.compile_from_source(shader_codes)
            self.valid = self.check_validate() and self.check_linked()
            if not self.valid:
                logger.error("%s material has been failed to compile from source" % self.name)

        if self.valid:
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

    def compile_from_source(self, shader_codes: dict):
        """
        :param shader_codes: {GL_VERTEX_SHADER:code_string, GL_FRAGMENT_SHADER:code_string, }
        """
        shaders = []
        for shader_type in shader_codes:
            shader = self.compile(shader_type, shader_codes[shader_type])
            if shader is not None:
                logger.info("Compile %s %s." % (self.name, shader_type))
                shaders.append(shader)

        self.program = glCreateProgram()

        # glProgramParameteri(self.program, GL_PROGRAM_SEPARABLE, GL_TRUE)
        glProgramParameteri(self.program, GL_PROGRAM_BINARY_RETRIEVABLE_HINT, GL_TRUE)

        for shader in shaders:
            glAttachShader(self.program, shader)

        glLinkProgram(self.program)

        for shader in shaders:
            glDetachShader(self.program, shader)
            glDeleteShader(shader)

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
        if shader_code == "" or shader_code is None:
            return None

        try:
            # Compile shaders
            shader = glCreateShader(shaderType)
            glShaderSource(shader, shader_code)
            glCompileShader(shader)
            compile_status = glGetShaderiv(shader, GL_COMPILE_STATUS)
            if compile_status != 1:
                infoLogs = glGetShaderInfoLog(shader)
                if infoLogs:
                    if type(infoLogs) == bytes:
                        infoLogs = infoLogs.decode("utf-8")

                    infoLogs = ("GL_COMPILE_STATUS : %d\n" % compile_status) + infoLogs
                    shader_code_lines = shader_code.split('\n')

                    infoLogs = infoLogs.split('\n')
                    for i, infoLog in enumerate(infoLogs):
                        error_line = re.match('\d\((\d+)\) : error', infoLog)
                        if error_line is not None:
                            # show prev 3 lines
                            error_line = int(error_line.groups()[0]) - 1
                            for num in range(max(0, error_line - 3), error_line):
                                infoLogs[i] += "\n\t    %s" % (shader_code_lines[num])
                            # show last line
                            infoLogs[i] += "\n\t--> %s" % (shader_code_lines[error_line])

                    infoLogs = "\n".join(infoLogs)

                    self.compile_message = "\n".join([self.compile_message, infoLogs])

                    logger.error("%s %s shader compile error.\n%s" % (self.name, shaderType.name, infoLogs))
            else:
                # complete
                logger.log(Logger.MINOR_INFO, "Complete %s %s compile." % (self.name, shaderType.name))
                return shader
        except:
            logger.error(traceback.format_exc())
        return None

    def check_validate(self):
        if self.program >= 0:
            glValidateProgram(self.program)
            validation = glGetProgramiv(self.program, GL_VALIDATE_STATUS)
            if validation == GL_TRUE:
                return True
            else:
                logger.warn("Validation failure (%s): %s" % (validation, glGetProgramInfoLog(self.program)))
        else:
            logger.warn("Validation failure : %s" % self.name)
        # always return True
        return True

    def check_linked(self):
        if self.program >= 0:
            link_status = glGetProgramiv(self.program, GL_LINK_STATUS)
            if link_status == GL_TRUE:
                return True
            else:
                logger.error("Link failure (%s): %s" % (link_status, glGetProgramInfoLog(self.program)))
        else:
            logger.error("Link failure : %s" % self.name)
        return False
