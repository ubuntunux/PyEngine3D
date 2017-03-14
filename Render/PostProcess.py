from OpenGL.GL import *

from Object import Quad
from Utilities import *


class PostProcess:
    def __init__(self):
        self.mesh = Quad()


class Tonemapping(PostProcess):
    def __init__(self):
        PostProcess.__init__(self)

    def initialize(self):
        pass

    def render(self):
        pass