from OpenGL.GL import *

from Core import logger
from Object import Quad
from Resource import ResourceManager
from Render.RenderTarget import RenderTargets, RenderTargetManager
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
        backbuffer = RenderTargetManager.instance().get_rendertarget(RenderTargets.BACKBUFFER)
        self.material_instance.set_uniform_data("texture_diffuse", backbuffer)

        texture_diffuse = RenderTargetManager.instance().get_rendertarget(RenderTargets.DIFFUSE)
        Render.Renderer.instance().framebuffer.bind_rendertarget(texture_diffuse, True, None, False)

        glClearColor(0.0, 0.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        PostProcess.render(self)

        # Render.Renderer.instance().framebuffer.bind_rendertarget(texture, None, False)

