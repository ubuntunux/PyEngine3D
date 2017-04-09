# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
import configparser
from collections import OrderedDict
import copy
import os
import re
import codecs
import traceback

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader

from Core import logger
import Resource
from Utilities import GetClassName, Attributes
from .UniformBuffer import CreateUniformBuffer, UniformTexture2D
from .ShaderParser import shader_parsing, ShaderCode

reFindUniform = re.compile("uniform\s+(.+?)\s+(.+?)\s*;")  # [Variable Type, Variable Name]


class Shader:
    def __init__(self, shaderName, file_path):
        logger.info("Create " + GetClassName(self) + " : " + shaderName)
        self.name = shaderName
        self.file_path = file_path

        # default shader macros
        self.macros = dict(MATERIAL_COMPONENTS=1)

        try:
            f = codecs.open(file_path, mode='r', encoding='utf-8')
            self.source = f.read()
            f.close()
        except:
            self.source = ""
            logger.info("Failed %s file open" % file_path)
        self.attribute = Attributes()

    def compile(self, shaderType, macros=None):
        """
        :param shaderType: GL_VERTEX_SHADER, GL_FRAGMENT_SHADER
        :param macros: dictionary
        """
        if self.source == "" or self.source is None:
            return

        # create macros
        combined_macros = copy.copy(macros) if macros is not None else dict()
        for macro in self.macros:
            combined_macros[macro] = self.macros[macro]

        if shaderType == GL_VERTEX_SHADER:
            combined_macros['VERTEX_SHADER'] = 1
        elif shaderType == GL_FRAGMENT_SHADER:
            combined_macros['FRAGMENT_SHADER'] = 1
        else:
            raise BaseException("Error!! Set valid shaderType.")
            return None

        shader = glCreateShader(shaderType)
        shader_file_dir = os.path.split(self.file_path)[0]
        # Shader source code parsing
        shader_code = shader_parsing(shader_file_dir, self.source, combined_macros)

        try:
            # Compile shaders
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

    def __del__(self):
        pass

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        return self.attribute


class Material:
    def __init__(self, combined_material_name, shader_name, macros: dict):
        self.valid = False
        logger.info("Create %s material." % combined_material_name)
        self.name = combined_material_name
        self.program = -1
        self.uniform_buffers = OrderedDict({})  # Declaration order is important.
        self.Attributes = Attributes()

        # build and link the program
        resourceMgr = Resource.ResourceManager.instance()
        shader = resourceMgr.getShader(shader_name)
        vertexShader = shader.compile(GL_VERTEX_SHADER, macros) if shader else None
        fragmentShader = shader.compile(GL_FRAGMENT_SHADER, macros) if shader else None

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

        material_contents = shader.get_material_contents()
        # material_contents = '''
        #     uniform int enable_blend;
        #     uniform float brightness;
        #     uniform vec4 emissive_color;
        #     uniform vec4 diffuse_color;
        #     uniform sampler2D texture_diffuse;
        #     uniform sampler2D texture_normal;
        #         '''

        uniform_contents = re.findall(reFindUniform, material_contents)
        for uniform_type, uniform_name in uniform_contents:
            uniform_buffer = CreateUniformBuffer(self.program, uniform_type, uniform_name)
            # Important : set texture binding index
            if uniform_buffer.__class__ == UniformTexture2D:
                uniform_buffer.set_texture_index(textureIndex)
                textureIndex += 1
            self.uniform_buffers[uniform_name] = uniform_buffer
        self.valid = True

    def __del__(self):
        pass

    def delete(self):
        glDeleteProgram(self.program)

    def useProgram(self):
        glUseProgram(self.program)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('type', type(self))
        return self.Attributes
