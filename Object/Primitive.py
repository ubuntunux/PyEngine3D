import os

import numpy as np
from OpenGL.GL import *

from Object import BaseObject, OBJ
from Utilities import *

# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
#------------------------------#
# CLASS : Primitive
#------------------------------#
class Primitive(BaseObject):
    position = np.array([], dtype=np.float32)
    color    = np.array([], dtype=np.float32)
    normal   = np.array([], dtype=np.float32)
    index = np.array([], dtype=np.uint32)
    none_offset = ctypes.c_void_p(0)
    initialized = False

    def __init__(self, name='', pos=(0,0,0), material=None):
        BaseObject.__init__(self, name, pos)

        # init variables
        self.material = material
        self.shader = self.material.shader

        self.position_buffer = -1
        self.color_buffer = -1
        self.normal_buffer = -1
        self.index_buffer = -1

        # binding buffers
        self.bindBuffers()

    def bindBuffers(self):
        # position buffer
        self.position_buffer = glGenBuffers(1) # Request a buffer slot from GPU
        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer) # Make this buffer the default one
        glBufferData(GL_ARRAY_BUFFER, self.position.nbytes, self.position, GL_STATIC_DRAW) # Upload data

        # color buffer
        self.color_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.color_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.color.nbytes, self.color, GL_STATIC_DRAW)

        # normal buffer
        self.normal_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.normal_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.normal.nbytes, self.normal, GL_STATIC_DRAW)

        # index buffer
        self.index_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index.nbytes, self.index, GL_STATIC_DRAW)

    def draw(self, cameraPos, view, perspective, lightPos, lightColor, selected=False):
        # update transform
        self.updateTransform()

        # use program
        glUseProgram(self.shader.program)

        loc = glGetUniformLocation(self.shader.program, "model")
        glUniformMatrix4fv(loc, 1, GL_FALSE, self.matrix)

        loc = glGetUniformLocation(self.shader.program, "view")
        glUniformMatrix4fv(loc, 1, GL_FALSE, view)

        loc = glGetUniformLocation(self.shader.program, "perspective")
        glUniformMatrix4fv(loc, 1, GL_FALSE, perspective)

        loc = glGetUniformLocation(self.shader.program, "diffuseColor")
        glUniform4fv(loc, 1, (0,0,0.5,1) if selected else (0.3, 0.3, 0.3, 1.0))

        # selected object render color
        loc = glGetUniformLocation(self.shader.program, "camera_position")
        glUniform3fv(loc, 1, cameraPos)

        # selected object render color
        loc = glGetUniformLocation(self.shader.program, "light_position")
        glUniform3fv(loc, 1, lightPos)

        # selected object render color
        loc = glGetUniformLocation(self.shader.program, "light_color")
        glUniform4fv(loc, 1, lightColor)


        # Binding buffers
        #loc = glGetAttribLocation(self.shader.program, "position")
        loc = 0
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, self.position.strides[0], self.none_offset)

        #loc = glGetAttribLocation(self.shader.program, "color")
        loc = 1
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.color_buffer)
        glVertexAttribPointer(loc, 4, GL_FLOAT, False, self.color.strides[0], self.none_offset)

        #loc = glGetAttribLocation(self.shader.program, "normal")
        loc = 2
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.normal_buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, self.normal.strides[0], self.none_offset)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
        glDrawElements(GL_TRIANGLES, self.index.nbytes, GL_UNSIGNED_INT, ctypes.c_void_p(0))
        glUseProgram(0)

#------------------------------#
# CLASS : StaticMesh
#------------------------------#
class StaticMesh(Primitive):
    def __init__(self, name='', pos=(0,0,0), material=None):
        obj = OBJ(os.path.join('Resources', 'Meshes', 'human.obj'), 1, True)
        self.position = np.array(obj.vertices, dtype=np.float32)
        self.color    = np.array(obj.vertices, dtype=np.float32)
        self.normal = np.array(obj.normals, dtype=np.float32)
        self.index = np.array(sum([i[0] for i in obj.faces], []), dtype=np.uint32)
        Primitive.__init__(self, name, pos, material)



#------------------------------#
# CLASS : DebugLine
#------------------------------#
class DebugLine:
    def __init__(self, pos1, pos2, width=2.5, color=(1,1,0)):
        self.width = width
        self.pos1 = pos1
        self.pos2 = pos2
        self.color = color

    def draw(self):
        glLineWidth(self.width)
        glColor3f(1,1,1)
        glBegin(GL_LINES)
        glVertex3f(*self.pos1)
        glVertex3f(*self.pos2)
        glEnd()

#------------------------------#
# CLASS : Triangle
#------------------------------#
class Triangle(Primitive):
    position = np.array([(-1,-1,0), (1,-1,0), (-1,1,0)], dtype=np.float32)
    color    = np.array([(1,0,0,1), (0,1,0,1), (0,0,1,1)], dtype=np.float32)
    normal = np.array([(0,-1,0), (1,-1,0), (-1,1,0)], dtype=np.float32)
    index = np.array([0,1,2], dtype=np.uint32)

#------------------------------#
# CLASS : Quad
#------------------------------#
class Quad(Primitive):
    position = np.array([ (-1,-1,1), (1,-1,1), (-1,1,1), (1,1,1) ], dtype=np.float32)
    color    = np.array([ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ], dtype=np.float32)
    normal = np.array([ (-1,-1,1), (1,-1,1), (-1,1,1), (1,1,1) ], dtype=np.float32)
    index = np.array([0,1,2,1,3,2], dtype=np.uint32)


#------------------------------#
# CLASS : Cube
#------------------------------#
class Cube(Primitive):
    color = np.array([ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1),
                (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ], dtype=np.float32)
    position = np.array([ (-1,-1,1),
                (1,-1,1),
                (1,1,1),
                (-1,1,1),
                (-1,-1,-1),
                (1,-1,-1),
                (1,1,-1),
                (-1,1,-1)], dtype=np.float32)
    normal = np.array([ (-1,-1,1),
                (1,-1,1),
                (1,1,1),
                (-1,1,1),
                (-1,-1,-1),
                (1,-1,-1),
                (1,1,-1),
                (-1,1,-1)], dtype=np.float32)
    index = np.array([0,1,2,
                        2,3,0,
                        1,5,6,
                        6,2,1,
                        7,6,5,
                        5,4,7,
                        4,0,3,
                        3,7,4,
                        4,5,1,
                        1,0,4,
                        3,2,6,
                        6,7,3], dtype=np.uint32)




#------------------------------#
# GLOBAL : primitives
#------------------------------#
primitives = [Triangle, Quad, Cube, StaticMesh]