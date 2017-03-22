from OpenGL.GL import *

from Core import logger
from Object import Quad
from Resource import ResourceManager
from Render.RenderTarget import RenderTargets, RenderTargetManager, copy_rendertarget
import Render


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

    def render(self):
        # texture = RenderTargetManager.instance().get_rendertarget(RenderTargets.BACKBUFFER)
        # texture_diffuse = RenderTargetManager.instance().get_rendertarget(RenderTargets.DIFFUSE)
        # Render.Renderer.instance().framebuffer.bind_rendertarget(texture_diffuse, None, False)
        # self.material_instance.set_uniform_data("texture_diffuse", texture)
        
        PostProcess.render(self, texture)

        # copy_rendertarget(texture_diffuse, texture)
        # Render.Renderer.instance().framebuffer.bind_rendertarget(texture, None, False)

