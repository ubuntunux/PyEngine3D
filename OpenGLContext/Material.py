import re
from collections import OrderedDict

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader
from OpenGL.arrays import GLbyteArray

import numpy as np

from Core import logger
import Resource
from Utilities import GetClassName, Attributes
from .UniformBuffer import CreateUniformBuffer, UniformTexture2D

reFindUniform = re.compile("uniform\s+(.+?)\s+(.+?)\s*;")  # [Variable Type, Variable Name]
reMacro = re.compile('\#(ifdef|ifndef|if|elif|else|endif)\s*(.*)')  # [macro type, expression]


class Material:
    def __init__(self, combined_material_name, shader, macros=None):
        self.valid = False
        logger.info("Create %s material." % combined_material_name)
        self.name = combined_material_name
        self.program = -1
        self.uniform_buffers = OrderedDict({})  # Declaration order is important.
        self.Attributes = Attributes()

        if shader:
            self.create_program(shader, macros=None)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('type', type(self))
        return self.Attributes

    def delete(self):
        glDeleteProgram(self.program)

    def useProgram(self):
        glUseProgram(self.program)

    def create_program(self, shader, macros=None):
        """
        :param shader: Shader class
        :param macros: dictionary
        """
        # build and link the program
        vertexShaderCode = shader.parsing_final_code(GL_VERTEX_SHADER, macros)
        fragmentShaderCode = shader.parsing_final_code(GL_FRAGMENT_SHADER, macros)

        vertexShader = self.compile(GL_VERTEX_SHADER, vertexShaderCode)
        fragmentShader = self.compile(GL_FRAGMENT_SHADER, fragmentShaderCode)

        if vertexShader is None or fragmentShader is None:
            logger.error("%s material compile error." % shader.name)
            return

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

        self.check_validate()
        self.check_linked()

        glShaderBinary 이것도 테스트 해보자.

        # test precompiled shader
        # format, result = self.retrieve()
        # print(self.program, format, result)
        # self.load(format, result)

        # create uniform buffers from source code
        self.create_uniform_buffers(self.program, vertexShaderCode, fragmentShaderCode)

        self.valid = True

    def retrieve(self):
        size = GLint()
        glGetProgramiv(self.program, GL_PROGRAM_BINARY_LENGTH, size)
        result = GLbyteArray.zeros((size.value,))
        size2 = GLint()
        format = GLenum()
        glGetProgramBinary(self.program, size.value, size2, format, result)
        return format.value, result

    def load(self, format, binary):
        glProgramBinary(self.program, format, binary, len(binary))
        #self.check_validate()
        #self.check_linked()

    def check_validate(self):
        glValidateProgram(self.program)
        validation = glGetProgramiv(self.program, GL_VALIDATE_STATUS)
        if validation == GL_FALSE:
            raise RuntimeError(
                """Validation failure (%s): %s""" % (
                    validation,
                    glGetProgramInfoLog(self.program),
                ))
        return self.program

    def check_linked(self):
        link_status = glGetProgramiv(self.program, GL_LINK_STATUS)
        if link_status == GL_FALSE:
            raise RuntimeError(
                """Link failure (%s): %s""" % (
                    link_status,
                    glGetProgramInfoLog(self.program),
                ))
        return self.program

    def create_uniform_buffers(self, program, *code_list):
        gather_code_lines = []
        for code in code_list:
            depth = 0
            is_in_material_block = False
            code_lines = code.splitlines()
            for code_line in code_lines:
                m = re.search(reMacro, code_line)
                # find macro
                if m is not None:
                    macro_type, macro_value = [group.strip() for group in m.groups()]
                    if macro_type in ('ifdef', 'ifndef', 'if'):
                        # increase depth
                        if is_in_material_block:
                            depth += 1
                        # start material block
                        elif macro_type == 'ifdef' and 'MATERIAL_COMPONENTS' == macro_value.split(" ")[0]:
                            is_in_material_block = True
                            depth = 1
                    elif macro_type == 'endif' and is_in_material_block:
                        depth -= 1
                        if depth == 0:
                            # exit material block
                            is_in_material_block = False
                # gather common code in material component
                elif is_in_material_block:
                    gather_code_lines.append(code_line)

        textureIndex = 0  # build uniform buffer variable
        material_contents = "\n".join(gather_code_lines)
        uniform_contents = re.findall(reFindUniform, material_contents)
        for uniform_type, uniform_name in uniform_contents:
            uniform_buffer = CreateUniformBuffer(program, uniform_type, uniform_name)
            if uniform_buffer is not None:
                # Important : set texture binding index
                if uniform_buffer.__class__ == UniformTexture2D:
                    uniform_buffer.set_texture_index(textureIndex)
                    textureIndex += 1
                self.uniform_buffers[uniform_name] = uniform_buffer
            else:
                logger.warn("%s shader has no %s uniform variable. (or maybe optimized by compiler.)" % (
                            shader.name, uniform_name))

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
                    logger.info("Complete %s %s compile." % (self.name, shaderType.name))
                    return shader
        except:
            logger.error(traceback.format_exc())
        return None
