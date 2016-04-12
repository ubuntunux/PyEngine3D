import os
import glob

import numpy as np
import pygame
from pygame import *

import OpenGL.GL as gl
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


# test code
if __name__ == '__main__':
    # reference - http://www.labri.fr/perso/nrougier/teaching/opengl
    data = np.zeros(4, dtype = [ ("position", np.float32, 4), ("color", np.float32, 4)] )
    data['position'] = [ (-1,-1,2,1), (+1,-1,2,1), (-1,+1,0,1), (+1,+1,0,1) ]
    data['color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]

    def create_object():
        buffer = gl.glGenBuffers(1) # Request a buffer slot from GPU
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer) # Make this buffer the default one
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data.nbytes, data, gl.GL_DYNAMIC_DRAW) # Upload data
        return buffer

    def render_object(shader, buffer):
        # bind buffer to shader
        stride = data.strides[0]
        offset = ctypes.c_void_p(0)
        loc = gl.glGetAttribLocation(shader, "position")
        gl.glEnableVertexAttribArray(loc)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)
        gl.glVertexAttribPointer(loc, 4, gl.GL_FLOAT, False, stride, offset)

        offset = ctypes.c_void_p(data.dtype["position"].itemsize)
        loc = gl.glGetAttribLocation(shader, "color")
        gl.glEnableVertexAttribArray(loc)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)
        gl.glVertexAttribPointer(loc, 4, gl.GL_FLOAT, False, stride, offset)

    # main
    pygame.init()
    width, height = 640, 480
    viewportRatio = float(width) / float(height)
    pygame.display.set_mode((width, height), OPENGL|DOUBLEBUF|RESIZABLE|HWPALETTE|HWSURFACE)
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, viewportRatio, 0.1, 100)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glClearColor(0, 0, 0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    # create shader
    shaderManager = ShaderManager.instance()
    shaderManager.initialize(None)
    shader = shaderManager.default_shader

    # create object buffer
    buffer = create_object()

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                running = False

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # render vertex buffer
        shader.useProgram()

        # render object - buffer binding to shdaer
        glLoadIdentity()
        glTranslatef(0, 0, -5)
        render_object(shader.program, buffer)

        # draw command
        glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

        glUseProgram(0)
        # swap buffer
        pygame.display.flip()