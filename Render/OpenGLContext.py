from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDetachShader

def create_shader():
    pass

def create_program(vertexShader, fragmentShader):
    program = glCreateProgram()
    glAttachShader(program, vertexShader)
    glAttachShader(program, fragmentShader)
    glLinkProgram(program)

    # delete shader
    glDetachShader(program, vertexShader)
    glDetachShader(program, fragmentShader)
    glDeleteShader(vertexShader)
    glDeleteShader(fragmentShader)
    return program