# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
import os, glob, traceback

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader, glDeleteShader

from Resource import *
from Core import logger
from Utilities import Singleton


#------------------------------#
# CLASS : Shader
#------------------------------#
class Shader:
    def __init__(self, shaderName, shaderSource, shaderType):
        logger.info("Create Shader : " + shaderName)
        self.name = shaderName
        self.source = shaderSource
        self.type = shaderType
        self.shader = glCreateShader(shaderType)

        # Set shaders source
        glShaderSource(self.shader, shaderSource)

        # Compile shaders
        glCompileShader(self.shader)

    def delete(self):
        glDeleteShader(self.shader)