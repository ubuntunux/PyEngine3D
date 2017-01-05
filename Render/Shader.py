# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
import os, glob, traceback

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader, glDeleteShader

from Resource import *
from Core import logger
from Utilities import Singleton, getClassName, Attributes


class Shader:
    shaderType = None

    def __init__(self, shaderName, shaderSource):
        logger.info("Create " + getClassName(self) + " : " + shaderName)
        self.name = shaderName
        self.source = shaderSource
        self.shader = glCreateShader(self.shaderType)
        self.attribute = Attributes()

        # Compile shaders
        try:
            glShaderSource(self.shader, shaderSource)
            glCompileShader(self.shader)
            if glGetShaderiv(self.shader, GL_COMPILE_STATUS) != 1 or True:
                infoLog = glGetShaderInfoLog(self.shader)
                if infoLog:
                    if type(infoLog) == bytes:
                        infoLog = infoLog.decode("utf-8")
                    logger.error("%s shader error!!!\n" % self.name + infoLog)
                else:
                    logger.info("%s shader complete." % self.name)
        except:
            print(traceback.format_exc())

    def getAttribute(self):
        self.attribute.setAttribute("name", self.name)
        return self.attribute

    def delete(self):
        glDeleteShader(self.shader)


class VertexShader(Shader):
    shaderType = GL_VERTEX_SHADER


class FragmentShader(Shader):
    shaderType = GL_FRAGMENT_SHADER