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
        self.buffer = -1
        self.buffer_index = -1
        self.data = None
        self.index = None
        self.initialized = 0
        self.initialize()

    def initialize(self):
        pass

    def bindBuffers(self):
        self.buffer = glGenBuffers(1) # Request a buffer slot from GPU
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer) # Make this buffer the default one
        glBufferData(GL_ARRAY_BUFFER, self.data.nbytes, self.data, GL_STATIC_DRAW) # Upload data

        # same for index buffer
        self.buffer_index = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.buffer_index)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index.nbytes, self.index, GL_STATIC_DRAW)

    def draw(self):
        # use program
        glUseProgram(self.shader.program)
        stride = self.data.strides[0]
        offset = ctypes.c_void_p(0)
        loc = glGetAttribLocation(self.shader.program, "position")
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
        glVertexAttribPointer(loc, 3, GL_FLOAT, False, stride, offset)

        offset = ctypes.c_void_p(self.data.dtype["position"].itemsize)
        loc = glGetAttribLocation(self.shader.program, "color")
        glEnableVertexAttribArray(loc)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
        glVertexAttribPointer(loc, 4, GL_FLOAT, False, stride, offset)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.buffer_index)
        glDrawElements(GL_TRIANGLES, self.index.nbytes, GL_UNSIGNED_INT, ctypes.c_void_p(0))
        glUseProgram(0)

#------------------------------#
# CLASS : Triangle
#------------------------------#
class Triangle(Primitive):
    """Triangle"""
    def initialize(self):
        self.data = np.zeros(3, [("position", np.float32, 3), ("color", np.float32, 4)] )
        self.data['position'] = [ (-1,-1,1), (1,-1,1), (-1,1,1)]
        self.data['color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1) ]
        self.index = np.array([0,1,2], dtype=np.uint32)

        # binding buffer
        self.bindBuffers()

        self.initialized = True

#------------------------------#
# CLASS : Quad
#------------------------------#
class Quad(Primitive):
    def initialize(self):
        self.data = np.zeros(4, [("position", np.float32, 3), ("color", np.float32, 4)] )
        self.data['position'] = [ (-1,-1,1), (1,-1,1), (-1,1,1), (1,1,1) ]
        self.data['color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
        self.index = np.array([0,1,2,1,3,2], dtype=np.uint32)
        # binding buffer
        self.bindBuffers()
        self.initialized = True



#------------------------------#
# CLASS : Cube
#------------------------------#
class Cube(Primitive):
    def initialize(self):
        if not self.initialized:
            self.data = np.zeros(8, [("position", np.float32, 3), ("color", np.float32, 4)])
            self.data['color']  = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1),
                                (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
            self.data['position'] = [ (-1,-1,1),
                                (1,-1,1),
                                (1,1,1),
                                (-1,1,1),
                                (-1,-1,-1),
                                (1,-1,-1),
                                (1,1,-1),
                                (-1,1,-1)]
            self.index = np.array([0,1,2,
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

            # binding buffer
            self.bindBuffers()
            self.initialized = True