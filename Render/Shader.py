import os
import glob

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader, glDeleteShader

from Core import logger
from Utilities import Singleton

shaderDirectory = os.path.join(os.path.split(__file__)[0], '..', 'Shader')

#------------------------------#
# CLASS : Shader
#------------------------------#
class Shader:
    # reference - http://www.labri.fr/perso/nrougier/teaching/opengl
    def __init__(self, name, vertex_code, fragment_code):
        logger.info("Create Shader : " + name)
        self.name = name
        self.program  = glCreateProgram()
        self.vertex   = glCreateShader(GL_VERTEX_SHADER)
        self.fragment = glCreateShader(GL_FRAGMENT_SHADER)

        # Set shaders source
        glShaderSource(self.vertex, vertex_code)
        glShaderSource(self.fragment, fragment_code)

        # Compile shaders
        glCompileShader(self.vertex)
        glCompileShader(self.fragment)

        # build and link the program
        glAttachShader(self.program, self.vertex)
        glAttachShader(self.program, self.fragment)
        glLinkProgram(self.program)

        # We can not get rid of shaders, they won't be used again
        glDetachShader(self.program, self.vertex)
        glDetachShader(self.program, self.fragment)

    def useProgram(self):
        glUseProgram(self.program)

    def delete(self):
        glDeleteShader(self.vertex)
        glDeleteShader(self.fragment)


#------------------------------#
# CLASS : ShaderManager
#------------------------------#
class ShaderManager(Singleton):
    def __init__(self):
        self.shaders = {}
        self.default_shader = None
        self.coreManager = None

    def initialize(self, coreManager):
        logger.info("initialize " + self.__class__.__name__)
        self.coreManager = coreManager

        # collect shader files
        shaderNames = set()
        for filename in glob.glob(os.path.join(shaderDirectory, '*.glsl')):
            filename = os.path.split(filename)[1]
            shaderNames.add(filename.split('_')[0])

        # create shader from files
        for shaderName in shaderNames:
            fileVS = open(os.path.join(shaderDirectory, shaderName + "_vs.glsl"), 'r')
            filePS = open(os.path.join(shaderDirectory, shaderName + "_ps.glsl"), 'r')
            vertex_code = fileVS.read()
            fragment_code = filePS.read()
            fileVS.close()
            filePS.close()
            shader = Shader(shaderName, vertex_code, fragment_code)
            self.shaders[shaderName] = shader
        # get default shader
        self.default_shader = self.getShader("default")

    def close(self):
        for key in self.shaders:
            shader = self.shaders[key]
            shader.delete()

    def getShader(self, shaderName):
        return self.shaders[shaderName]