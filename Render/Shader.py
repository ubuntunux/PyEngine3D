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


SIMPLE_VERTEX_SHADER = '''
#version 330
in vec4 position;
void main()
{
   gl_Position = position;
}'''

SIMPLE_FRAGMENT_SHADER = '''
#version 330
void main()
{
   gl_FragColor = vec4(1.0f, 0.0f, 1.0f, 1.0f);
}'''

DEFAULT_VERTEX_SHADER = '''
attribute vec4 position;
attribute vec4 color;
varying vec4 v_color;
varying vec3 normal;
void main() {
    v_color = color;
    normal = gl_NormalMatrix * gl_Normal;
    gl_Position = gl_ModelViewProjectionMatrix * position * 0.2f;
}'''

DEFAULT_FRAGMENT_SHADER = '''
varying vec4 v_color;
varying vec3 normal;
void main() {
    float intensity;
    vec4 color;
    vec3 n = normalize(normal);
    vec3 l = normalize(gl_LightSource[0].position).xyz;
    intensity = saturate(dot(l, n));
    color = gl_LightSource[0].ambient + gl_LightSource[0].diffuse * intensity;
    gl_FragColor = v_color;
}'''

TEXTURE_FRAGMENT_SHADER = '''
#version 140 // OpenGL 3.1
varying vec2 vCoord;			// vertex texture coordinates
uniform sampler2D diffuseTex;  // alpha mapped texture
uniform vec4 diffuseColor;		// actual color for this text
void main(void)
{
	// multiply alpha with the font texture value
	gl_FragColor = vec4(diffuseColor.rgb, texture2D(diffuseTex, vCoord).r * diffuseColor.a);
}
'''

#------------------------------#
# CLASS : Shader
#------------------------------#
class Shader:
    # reference - http://www.labri.fr/perso/nrougier/teaching/opengl
    def __init__(self, name, vertex_code, fragment_code):
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
        self.createShader("default", DEFAULT_VERTEX_SHADER, DEFAULT_FRAGMENT_SHADER)
        self.default_shader = self.getShader("default")

    def close(self):
        for key in self.shaders:
            shader = self.shaders[key]
            shader.delete()

    def createShader(self, shaderName, vertexShader, fragmentShader):
        shader = Shader(shaderName, vertexShader, fragmentShader)
        self.shaders[shaderName] = shader

    def getShader(self, shaderName):
        return self.shaders[shaderName]


# test code
if __name__ == '__main__':
    # reference - http://www.labri.fr/perso/nrougier/teaching/opengl
    data = np.zeros(4, dtype = [ ("position", np.float32, 4), ("color", np.float32, 4)] )
    data['color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
    data['position'] = [ (-1,-1,0,1), (+1,-1,0,1), (-1,+1,0,1), (+1,+1,0,1) ]

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
        gl.glVertexAttribPointer(loc, 3, gl.GL_FLOAT, False, stride, offset)

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