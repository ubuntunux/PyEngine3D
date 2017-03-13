from OpenGL.GL import *

from Object import Quad
from Utilities import *


class PostProcess(Quad):
    def __init__(self):
        Quad.__init__(self)
        self.position = np.array([(-1, -1, 0), (1, -1, 0), (-1, 1, 0), (1, 1, 0)], dtype=np.float32)
        self.color = np.array([(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (1, 1, 0, 1)], dtype=np.float32)
        self.normal = np.array([(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)], dtype=np.float32)
        self.texcoord = np.array([(0, 0), (1, 0), (0, 1), (1, 1)], dtype=np.float32)
        self.index = np.array([0, 1, 2, 1, 3, 2], dtype=np.uint32)
        self.computeTangent()
        self.initialize()


class Tonemapping(PostProcess):
    def __init__(self):
        PostProcess.__init__(self)

    def initialize(self):
        pass

    def render(self):
        pass