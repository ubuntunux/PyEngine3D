from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader

import Resource
from Core import logger
from Utilities import Attributes


class Material:
    def __init__(self, materialName, vs, fs):
        logger.info("Create Material : " + materialName)
        self.name = materialName
        self.twoSide = False
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

        # TEST_CODE : material components
        self.diffuseColorBind = glGetUniformLocation(self.program, "diffuseColor")
        self.textureDiffuseBind = glGetUniformLocation(self.program, "textureDiffuse")
        self.textureNormalBind = glGetUniformLocation(self.program, "textureNormal")
        self.textureDiffuse = Resource.ResourceManager.instance().getTextureID("wool_d")
        self.textureNormal = Resource.ResourceManager.instance().getTextureID("wool_n")

    def bind(self, selected):
        # TEST_CODE : material components
        glUniform4fv(self.diffuseColorBind, 1, (0, 0, 0.5, 1) if selected else (0.3, 0.3, 0.3, 1.0))

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.textureDiffuse)
        glUniform1i(self.textureDiffuseBind, 0)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.textureNormal)
        glUniform1i(self.textureNormalBind, 1)

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
