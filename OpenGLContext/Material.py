from collections import OrderedDict

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader
from OpenGL.arrays import GLbyteArray

import numpy as np

from Utilities import GetClassName, Attributes, Logger
from .UniformBuffer import CreateUniformBuffer, UniformTexture2D
from Common import logger


class Material:
    def __init__(self, material_name, material_datas={}):
        self.valid = False
        logger.info("Load %s material." % material_name)

        vertex_shader_code = material_datas.get('vertex_shader_code', "")
        fragment_shader_code = material_datas.get('fragment_shader_code', "")
        uniforms = material_datas.get('uniforms', [])
        self.material_component_names = [x[1] for x in material_datas.get('material_components', [])]
        self.macros = material_datas.get('macros', {})

        self.name = material_name
        self.lastTextureIndex = 0
        self.program = -1
        self.uniform_buffers = OrderedDict({})  # Declaration order is important.
        self.Attributes = Attributes()
        self.valid = self.create_program(vertex_shader_code, fragment_shader_code, uniforms)

        if not self.valid:
            logger.error("Failed create %s material." % self.name)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('type', type(self))
        return self.Attributes

    def delete(self):
        glDeleteProgram(self.program)

    def useProgram(self):
        glUseProgram(self.program)

    def create_uniform_buffer(self, uniform_type, uniform_name):
        uniform_buffer = CreateUniformBuffer(self.program, uniform_type, uniform_name)
        if uniform_buffer is not None:
            # Important : set texture binding index
            if uniform_buffer.__class__ == UniformTexture2D:
                uniform_buffer.set_texture_index(self.lastTextureIndex)
                self.lastTextureIndex += 1
            self.uniform_buffers[uniform_name] = uniform_buffer
        else:
            logger.warn("%s material has no %s uniform variable. (or maybe optimized by compiler.)" % (
                self.name, uniform_name))

    def create_program(self, vertexShaderCode, fragmentShaderCode, uniforms):
        """
        :param vertexShaderCode: string
        :param fragmentShaderCode: sring
        :param uniforms: [ (uniform_type, uniform_name), ... ]
        """
        vertexShader = self.compile(GL_VERTEX_SHADER, vertexShaderCode)
        fragmentShader = self.compile(GL_FRAGMENT_SHADER, fragmentShaderCode)

        if vertexShader is None or fragmentShader is None:
            return False

        # create program
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

        if not self.check_validate():
            return False

        if not self.check_linked():
            return False

        # create uniform buffers from source code
        for uniform_type, uniform_name in uniforms:
            self.create_uniform_buffer(uniform_type, uniform_name)
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

    def save_to_binary(self):
        size = GLint()
        glGetProgramiv(self.program, GL_PROGRAM_BINARY_LENGTH, size)
        result = np.zeros(size.value)
        size2 = GLint()
        format = GLenum()
        glGetProgramBinary(self.program, size.value, size2, format, result)
        return format, result

    def load_from_binary(self, format:GLenum, binary:np.array):
        glProgramBinary(self.program, format.value, binary, len(binary))
        self.check_validate()
        self.check_linked()

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
