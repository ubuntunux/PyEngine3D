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
    shaderType = None

    def __init__(self, shaderName, shaderSource):
        logger.info("Create " + self.__class__.__name__ + " : " + shaderName)
        self.name = shaderName
        self.source = shaderSource
        self.shader = glCreateShader(self.shaderType)

        # Set shaders source
        glShaderSource(self.shader, shaderSource)

        # Compile shaders
        glCompileShader(self.shader)

    def delete(self):
        glDeleteShader(self.shader)

#------------------------------#
# CLASS : VertexShader
#------------------------------#
class VertexShader(Shader):
    shaderType = GL_VERTEX_SHADER

#------------------------------#
# CLASS : FragmentShader
#------------------------------#
class FragmentShader(Shader):
    shaderType = GL_FRAGMENT_SHADER