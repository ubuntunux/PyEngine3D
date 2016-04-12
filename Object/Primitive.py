import numpy as np

from OpenGL.GL import *

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


class Primitive:
    def __init__(self, name='', pos=(0,0,0), material=None):
        self.name = name
        self.pos = np.array(pos)
        self.material = material
        self.shader = self.material.shader
        self.buffer = 0
        self.data = None
        self.initialize()

    def initialize(self):
        pass

    def draw(self):
        pass

class Triangle(Primitive):
    """Triangle"""
    def draw(self):
        glBegin(GL_POLYGON)
        glVertex3f(-1.0, -1.0, 0.0)
        glVertex3f(1.0, -1.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)
        glEnd()

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

        # draw command
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glUseProgram(0)

class Sphere(Primitive):
    """Sphere"""
    def __init__(self, *args, segment=4, **kargs):
        super(Sphere, self).__init__(*args, **kargs)
        self.segment = segment

    def draw(self):
        glBegin(GL_QUADS)
        glVertex3f(-1.0, -1.0, 0.0)
        glVertex3f(1.0, -1.0, 0.0)
        glVertex3f(1.0, 1.0, 0.0)
        glVertex3f(-1.0, 1.0, 0.0)
        glEnd()
