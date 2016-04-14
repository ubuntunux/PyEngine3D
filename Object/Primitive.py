import numpy as np

from OpenGL.GL import *

# reference - http://www.labri.fr/perso/nrougier/teaching/opengl
#------------------------------#
# CLASS : Primitive
#------------------------------#
class Primitive:
    def __init__(self, name='', pos=(0,0,0), material=None):
        self.name = name
        self.pos = np.array(pos)
        self.material = material
        self.shader = self.material.shader
        self.buffer = 0
        self.data = None
        self.initialized = 0
        self.initialize()

    def initialize(self):
        pass

    def draw(self):
        pass

#------------------------------#
# CLASS : Triangle
#------------------------------#
class Triangle(Primitive):
    """Triangle"""
    def draw(self):
        glBegin(GL_POLYGON)
        glVertex3f(-1.0, -1.0, 0.0)
        glVertex3f(1.0, -1.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)
        glEnd()

#------------------------------#
# CLASS : Quad
#------------------------------#
class Quad(Primitive):
    def initialize(self):
        self.data = np.zeros(4, dtype = [ ("position", np.float32, 4), ("color", np.float32, 4)] )
        self.data['position'] = [ (-1,-1,0,1), (1,-1,0,1), (-1,1,0,1), (1,1,0,1) ]
        self.data['color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]

        self.buffer = glGenBuffers(1) # Request a buffer slot from GPU
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer) # Make this buffer the default one
        glBufferData(GL_ARRAY_BUFFER, self.data.nbytes, self.data, GL_DYNAMIC_DRAW) # Upload data

    """Quad"""
    def draw(self):
        # use program
        self.shader.useProgram()

        glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
        '''

        # bind buffer to shader
        stride = self.data.strides[0]
        offset = ctypes.c_void_p(0)
        loc = glGetAttribLocation(self.shader.program, "position")
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, stride, offset)
        # bind color
        offset = ctypes.c_void_p(self.data.dtype["position"].itemsize)
        loc = glGetAttribLocation(self.shader.program, "color")
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
        glVertexAttribPointer(loc, 4, GL_FLOAT, False, stride, offset)
        '''

        # draw command
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glUseProgram(0)

#------------------------------#
# CLASS : Cube
#------------------------------#
class Cube(Primitive):
    s=0.5
    vertices=[
            -s, -s, -s,
             s, -s, -s,
             s,  s, -s,
            -s,  s, -s,
            -s, -s,  s,
             s, -s,  s,
             s,  s,  s,
            -s,  s,  s,
            ]
    colors=[
            0, 0, 0,
            1, 0, 0,
            0, 1, 0,
            0, 0, 1,
            0, 1, 1,
            1, 0, 1,
            1, 1, 1,
            1, 1, 0,
            ]
    indices=[
            0, 1, 2, 2, 3, 0,
            0, 4, 5, 5, 1, 0,
            1, 5, 6, 6, 2, 1,
            2, 6, 7, 7, 3, 2,
            3, 7, 4, 4, 0, 3,
            4, 7, 6, 6, 5, 4,
            ]

    def initialize(self):
        if not self.initialized:
            self.buffers = glGenBuffers(3)
            glBindBuffer(GL_ARRAY_BUFFER, self.buffers[0])
            glBufferData(GL_ARRAY_BUFFER,
                    len(self.vertices)*4,  # byte size
                    (ctypes.c_float*len(self.vertices))(*self.vertices), # 謎のctypes
                    GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, self.buffers[1])
            glBufferData(GL_ARRAY_BUFFER,
                    len(self.colors)*4, # byte size
                    (ctypes.c_float*len(self.colors))(*self.colors),  # 謎のctypes
                    GL_STATIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.buffers[2])
            glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                    len(self.indices)*4, # byte size
                    (ctypes.c_uint*len(self.indices))(*self.indices),  # 謎のctypes
                    GL_STATIC_DRAW)
            self.initialized = True

    """Quad"""
    def draw(self):
        # use program
        glUseProgram(self.shader.program)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffers[0])
        glVertexPointer(3, GL_FLOAT, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffers[1])
        glColorPointer(3, GL_FLOAT, 0, None)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.buffers[2])
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glUseProgram(0)