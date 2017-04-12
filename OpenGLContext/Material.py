import re
from collections import OrderedDict

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader

from Core import logger
import Resource
from Utilities import GetClassName, Attributes
from .UniformBuffer import CreateUniformBuffer, UniformTexture2D

reFindUniform = re.compile("uniform\s+(.+?)\s+(.+?)\s*;")  # [Variable Type, Variable Name]


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
            logger.error("%s material compile error." % shader_name)
            return

        # create program
        self.program = glCreateProgram()
        glAttachShader(self.program, vertexShader)
        glAttachShader(self.program, fragmentShader)
        glLinkProgram(self.program)

        # delete shader
        glDetachShader(self.program, vertexShader)
        glDetachShader(self.program, fragmentShader)
        glDeleteShader(vertexShader)
        glDeleteShader(fragmentShader)

        # build uniform buffer variable
        textureIndex = 0

        # material_contents = shader.get_material_contents()
        material_contents = '''
            uniform int enable_blend;
            uniform float brightness;
            uniform vec4 emissive_color;
            uniform vec4 diffuse_color;
            uniform sampler2D texture_diffuse;
            uniform sampler2D texture_normal;
                '''

        uniform_contents = re.findall(reFindUniform, material_contents)
        for uniform_type, uniform_name in uniform_contents:
            uniform_buffer = CreateUniformBuffer(self.program, uniform_type, uniform_name)
            if uniform_buffer is not None:
                # Important : set texture binding index
                if uniform_buffer.__class__ == UniformTexture2D:
                    uniform_buffer.set_texture_index(textureIndex)
                    textureIndex += 1
                self.uniform_buffers[uniform_name] = uniform_buffer
            else:
                logger.warn("%s shader has no %s uniform variable. (or maybe optimized by compiler.)" % (
                            shader.name, uniform_name))
        self.valid = True

    def compile(self, shaderType, shader_code):
        """
        :param shaderType: GL_VERTEX_SHADER, GL_FRAGMENT_SHADER
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
