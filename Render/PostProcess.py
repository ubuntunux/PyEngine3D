from OpenGL.GL import *

from Core import logger
from OpenGLContext import RenderTargets, RenderTargetManager
from ResourceManager import ResourceManager
from Render import Renderer


class PostProcess:
    def __init__(self, name, material_instance):
        logger.info("Create PostProcess : %s" % name)
        self.name = name
        self.mesh = ResourceManager.ResourceManager.instance().getMesh("Quad")
        self.geometry = self.mesh.get_geometry_instances(self)[0]
        self.geometry.set_material_instance(material_instance)
        self.material_instance = material_instance

    def render(self):
        self.material_instance.useProgram()
        self.material_instance.bind_material_instance()
        self.geometry.bindBuffers()
        self.geometry.draw()


class CopyRenderTarget(PostProcess):
    def __init__(self, name):
        material_instance = ResourceManager.ResourceManager.instance().getMaterialInstance("copy_rendertarget")
        PostProcess.__init__(self, name, material_instance)

    def render(self, src_texture, dst_texture):
        Render.Renderer.instance().framebuffer.bind_rendertarget(dst_texture, False, None, False)
        texture_diffuse = RenderTargetManager.instance().get_rendertarget(src_texture)
        self.material_instance.set_uniform_data("texture_diffuse", texture_diffuse)
        PostProcess.render(self)


class Tonemapping(PostProcess):
    def __init__(self, name):
        material_instance = ResourceManager.ResourceManager.instance().getMaterialInstance("tonemapping")
        PostProcess.__init__(self, name, material_instance)

    def render(self):
        backbuffer = RenderTargetManager.instance().get_rendertarget(RenderTargets.BACKBUFFER)
        self.material_instance.set_uniform_data("texture_diffuse", backbuffer)

        texture_diffuse = RenderTargetManager.instance().get_rendertarget(RenderTargets.DIFFUSE)
        Renderer.instance().framebuffer.bind_rendertarget(texture_diffuse, True, None, False)
        
        PostProcess.render(self)
