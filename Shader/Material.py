import re

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader

import Resource
from Core import logger
from Utilities import Attributes
from Shader import *

shader = """
void main()
{
}
"""

m = re.sub("void\s*main\s*\(\s*\)",
           "\n\n/* Begin : Material Template */\n%s\n/* End : Material Template */\n\nvoid main()" % "here", shader, 1)


class Material:
    def __init__(self, material_name, vs, fs):
        logger.info("Create Material : " + material_name)
        resourceMgr = Resource.ResourceManager.instance()
        self.name = material_name
        self.activateTextureIndex = GL_TEXTURE0
        self.textureIndex = 0
        self.Attributes = Attributes()

        # build and link the program
        self.program = glCreateProgram()
        self.vertexShader = vs
        self.fragmentShader = fs
        glAttachShader(self.program, vs.shader)
        glAttachShader(self.program, fs.shader)
        glLinkProgram(self.program)

        # We can not get rid of shaders, they won't be used again
        glDetachShader(self.program, vs.shader)
        glDetachShader(self.program, fs.shader)

        # TODO : build material components from shader files parsing.
        self.diffuseColor = UniformColor(self.program, "diffuseColor", (1.0, 1.0, 1.0, 1.0))
        self.textureDiffuse = UniformTexture2D(self.program, "textureDiffuse", resourceMgr.getTexture("wool_d"))
        self.textureNormal = UniformTexture2D(self.program, "textureNormal", resourceMgr.getTexture("wool_n"))

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDetachShader(self.program, self.vertexShader.shader)
        glDetachShader(self.program, self.fragmentShader.shader)
        self.vertexShader.delete()
        self.fragmentShader.delete()
        glDeleteProgram(self.program)

    def bind(self):
        # TODO : auto bind uniform variables.
        self.diffuseColor.bind()

        # very important. must reset_texture_index first!!
        self.reset_texture_index()
        self.bind_texture(self.textureNormal)
        self.bind_texture(self.textureDiffuse)

    def reset_texture_index(self):
        self.activateTextureIndex = GL_TEXTURE0
        self.textureIndex = 0

    def bind_texture(self, texture):
        texture.bind(self.activateTextureIndex, self.textureIndex)
        self.activateTextureIndex += 1
        self.textureIndex += 1

    def getVertexShader(self):
        return self.vertexShader

    def getFragmentShader(self):
        return self.fragmentShader

    def useProgram(self):
        glUseProgram(self.program)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('fragmentShader', self.fragmentShader.name, type(self.fragmentShader))
        self.Attributes.setAttribute('vertexShader', self.vertexShader.name, type(self.vertexShader))
        return self.Attributes


class MaterialInstance:
    resourceMgr = None

    def __init__(self, material_instance_name, vs, fs):
        logger.info("Create Material Instance : " + material_instance_name)
        self.name = material_instance_name
        self.activateTextureIndex = GL_TEXTURE0
        self.textureIndex = 0
        self.Attributes = Attributes()

        resourceMgr = Resource.ResourceManager.instance()

        # build and link the program
        self.program = glCreateProgram()
        self.vertexShader = vs
        self.fragmentShader = fs
        glAttachShader(self.program, vs.shader)
        glAttachShader(self.program, fs.shader)
        glLinkProgram(self.program)

        # We can not get rid of shaders, they won't be used again
        glDetachShader(self.program, vs.shader)
        glDetachShader(self.program, fs.shader)

        # TODO : build material components from shader files parsing.
        self.floatBrightness = np.float32(1.0)
        self.uniformFloatBrightness = UniformFloat(self.program, "brightness")
        self.colorDiffuse = np.array((1.0, 1.0, 1.0, 1.0), dtype=np.float32)
        self.uniformColorDiffuse = UniformColor(self.program, "diffuseColor")
        self.uniformTextureDiffuse = UniformTexture2D(self.program, "textureDiffuse")
        self.uniformTextureNormal = UniformTexture2D(self.program, "textureNormal")
        self.textureDiffuse = resourceMgr.getTexture("wool_d")
        self.textureNormal = resourceMgr.getTexture("wool_n")

    def __del__(self):
        pass
        # self.delete()

    def delete(self):
        glDetachShader(self.program, self.vertexShader.shader)
        glDetachShader(self.program, self.fragmentShader.shader)
        self.vertexShader.delete()
        self.fragmentShader.delete()
        glDeleteProgram(self.program)

    def bind(self):
        # TODO : auto bind uniform variables.
        self.uniformFloatBrightness.bind(self.floatBrightness)
        self.uniformColorDiffuse.bind(self.colorDiffuse)

        # very important. must reset_texture_index first!!
        self.reset_texture_index()
        self.bind_texture(self.uniformTextureNormal, self.textureNormal)
        self.bind_texture(self.uniformTextureDiffuse, self.textureDiffuse)

    def reset_texture_index(self):
        self.activateTextureIndex = GL_TEXTURE0
        self.textureIndex = 0

    def bind_texture(self, uniform_texture, texture):
        uniform_texture.bind(self.activateTextureIndex, self.textureIndex, texture)
        self.activateTextureIndex += 1
        self.textureIndex += 1

    def getVertexShader(self):
        return self.vertexShader

    def getFragmentShader(self):
        return self.fragmentShader

    def useProgram(self):
        glUseProgram(self.program)

    def getAttribute(self):
        self.Attributes.setAttribute('name', self.name)
        self.Attributes.setAttribute('fragmentShader', self.fragmentShader.name, type(self.fragmentShader))
        self.Attributes.setAttribute('vertexShader', self.vertexShader.name, type(self.vertexShader))
        return self.Attributes
