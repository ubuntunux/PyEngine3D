import os
import configparser
from collections import OrderedDict
import re
import traceback

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader

import Resource
from Core import logger
from Utilities import Attributes
from Material import *

reFindUniform = re.compile("uniform\s+(.+?)\s+(.+?)\s*;")


class Material:
    def __init__(self, material_name, material_template):
        self.loaded = False
        logger.info("Create Material : " + material_name)
        resourceMgr = Resource.ResourceManager.instance()
        self.name = material_name
        self.material_template = material_template
        self.uniforms = OrderedDict({})
        self.activateTextureIndex = GL_TEXTURE0
        self.textureIndex = 0
        self.program = -1
        self.Attributes = Attributes()

        # build and link the program
        vs = resourceMgr.getVertexShader("default")
        fs = resourceMgr.getFragmentShader("default")
        self.vertexShader = vs.compile(self.material_template)
        self.fragmentShader = fs.compile(self.material_template)

        if self.vertexShader is None or self.fragmentShader is None:
            logger.error("%s material compile error." % material_name)
            return

        # create program
        self.program = glCreateProgram()
        glAttachShader(self.program, self.vertexShader)
        glAttachShader(self.program, self.fragmentShader)
        glLinkProgram(self.program)
        glDetachShader(self.program, self.vertexShader)
        glDetachShader(self.program, self.fragmentShader)

        # create uniform variables
        uniforms = re.findall(reFindUniform, self.material_template)
        for uniform_type, uniform_name in uniforms:
            uniform_class = None
            if uniform_type == "float":
                uniform_class = UniformFloat
            elif uniform_type == "vec2":
                uniform_class = UniformVector2
            elif uniform_type == "vec3":
                uniform_class = UniformVector3
            elif uniform_type == "vec4":
                uniform_class = UniformVector4
            elif uniform_type == "sampler2D":
                uniform_class = UniformTexture2D

            self.uniforms[uniform_name] = uniform_class(self.program, uniform_name)
        self.loaded = True

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDeleteProgram(self.program)
        glDeleteShader(self.vertexShader)
        glDeleteShader(self.fragmentShader)

    def useProgram(self):
        glUseProgram(self.program)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        return self.Attributes


class MaterialInstance:
    resourceMgr = None

    def __init__(self, material_instance_name, filePath):
        self.loaded = False
        logger.info("Create Material Instance : " + material_instance_name)
        resourceMgr = Resource.ResourceManager.instance()
        self.name = material_instance_name
        self.program = None
        self.activateTextureIndex = GL_TEXTURE0
        self.textureIndex = 0
        self.Attributes = Attributes()

        # open material instance file
        material_inst_file = configparser.ConfigParser()
        material_inst_file.read(filePath)
        logger.info("Load Material Instance : %s" % os.path.split(filePath)[1])

        # get material
        material_name = material_inst_file.get('Material', 'name')
        self.material = resourceMgr.getMaterial(material_name)
        if self.material is None:
            return
        self.program = self.material.program

        # get uniform variable values
        self.variables = {}
        for value_type in material_inst_file.sections():
            if value_type == 'Material':
                continue
            for value_name in material_inst_file[value_type]:
                strValue = material_inst_file.get(value_type, value_name)
                value = conversion(value_type, strValue)
                if value is not None:
                    self.variables[value_name] = value
                else:
                    logger.error("%s MaterialInstance, %s %s is none." % (self.name, value_type, value_name))
        self.loaded = True

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        pass

    def bind(self):
        # TODO : auto bind uniform variables.
        self.material.uniforms['brightness'].bind(self.variables['brightness'])
        self.material.uniforms['diffuse_color'].bind(self.variables['diffuse_color'])

        # very important. must reset_texture_index first!!
        self.reset_texture_index()
        self.bind_texture(self.material.uniforms['texture_diffuse'], self.variables['texture_diffuse'])
        self.bind_texture(self.material.uniforms['texture_normal'], self.variables['texture_normal'])

    def reset_texture_index(self):
        self.activateTextureIndex = GL_TEXTURE0
        self.textureIndex = 0

    def bind_texture(self, uniform_texture, texture):
        uniform_texture.bind(self.activateTextureIndex, self.textureIndex, texture)
        self.activateTextureIndex += 1
        self.textureIndex += 1

    def getProgram(self):
        return self.material.program

    def useProgram(self):
        glUseProgram(self.material.program)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('material', self.material.name, type(self.material))
        return self.Attributes
