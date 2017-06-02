from OpenGL.GL import *

from Common import logger
from App import CoreManager
from Object import ScreenQuad
from OpenGLContext import RenderTargets, RenderTargetManager


class PostProcess:
    def __init__(self, name, material_instance):
        logger.info("Create PostProcess : %s" % name)
        self.name = name
        self.mesh = CoreManager.instance().resource_manager.getMesh("Quad")
        self.geometry = ScreenQuad(self.mesh.vertex_buffers[0], material_instance)
        self.material_instance = material_instance

    def render(self):
        self.material_instance.useProgram()
        self.material_instance.bind_material_instance()
        self.geometry.bindBuffers()
        self.geometry.draw()


class CopyRenderTarget(PostProcess):
    def __init__(self, name):
        material_instance = CoreManager.instance().resource_manager.getMaterialInstance("copy_rendertarget")
        PostProcess.__init__(self, name, material_instance)

    def render(self, src_texture, dst_texture):
        CoreManager.instance().renderer.framebuffer.bind_rendertarget(dst_texture, False, None, False)
        texture_diffuse = RenderTargetManager.instance().get_rendertarget(src_texture)
        self.material_instance.set_uniform_data("texture_diffuse", texture_diffuse)
        PostProcess.render(self)


class Tonemapping(PostProcess):
    def __init__(self, name):
        material_instance = CoreManager.instance().resource_manager.getMaterialInstance("tonemapping")
        PostProcess.__init__(self, name, material_instance)

    def render(self):
        backbuffer = RenderTargetManager.instance().get_rendertarget(RenderTargets.BACKBUFFER)
        self.material_instance.set_uniform_data("texture_diffuse", backbuffer)

        texture_diffuse = RenderTargetManager.instance().get_rendertarget(RenderTargets.DIFFUSE)
        CoreManager.instance().renderer.framebuffer.bind_rendertarget(texture_diffuse, True, None, False)
        PostProcess.render(self)
