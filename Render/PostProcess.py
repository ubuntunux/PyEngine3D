from OpenGL.GL import *

from Core import logger
from Object import Quad
from Resource import ResourceManager


class PostProcess:
    def __init__(self, name, material_instance):
        logger.info("Create PostProcess : %s" % name)
        self.name = name
        self.mesh = ResourceManager.ResourceManager.instance().getMesh("quad")
        self.material_instance = material_instance
        self.program = self.material_instance.program

    def render(self):
        glUseProgram(self.program)
        self.material_instance.bind()
        self.mesh.bindBuffers()
        self.mesh.draw()


class Tonemapping(PostProcess):
    def __init__(self, name):
        material_instance = ResourceManager.ResourceManager.instance().getMaterialInstance("tonemapping")
        PostProcess.__init__(self, name, material_instance)