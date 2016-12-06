from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader

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
