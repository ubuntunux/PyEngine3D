# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
import os, glob, traceback

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader, glDeleteShader

from Resource import *
from Core import logger
from Utilities import Singleton, getClassName


class Shader:
    """
    CLASS : Shader
    """

    shaderType = None

    def __init__(self, shaderName, shaderSource):
        logger.info("Create " + getClassName(self) + " : " + shaderName)
        self.name = shaderName
        self.source = shaderSource
        self.shader = glCreateShader(self.shaderType)

        # Set shaders source
        glShaderSource(self.shader, shaderSource)

        # Compile shaders
        glCompileShader(self.shader)

    def delete(self):
        glDeleteShader(self.shader)


class VertexShader(Shader):
    """
    CLASS : VertexShader
    """
    shaderType = GL_VERTEX_SHADER


class FragmentShader(Shader):
    """
    CLASS : FragmentShader
    """
    shaderType = GL_FRAGMENT_SHADER