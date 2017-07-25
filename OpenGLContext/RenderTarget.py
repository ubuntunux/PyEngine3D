from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from Utilities import Singleton, GetClassName, Attributes, AutoEnum
from Common import logger
from .Texture import Texture2D


class RenderTargets(AutoEnum):
    BACKBUFFER = ()
    WORLD_NORMAL = ()
    DEPTHSTENCIL = ()
    DIFFUSE = ()
    SHADOWMAP = ()
    COUNT = ()


class RenderTargetManager(Singleton):
    name = "RenderTargetManager"

    def __init__(self):
        self.core_manager = None
        self.rendertargets = []

    def initialize(self, core_manager):
        logger.info("initialize " + GetClassName(self))
        self.core_manager = core_manager
        self.clear()

    def clear(self):
        self.rendertargets = [None, ] * RenderTargets.COUNT.value

    def get_rendertarget(self, texture_enum: RenderTargets) -> Texture2D:
        return self.rendertargets[texture_enum.value]

    def create_rendertarget(self, rendertarget_enum, **kwargs):
        rendertarget = Texture2D(name=str(rendertarget_enum), **kwargs)
        self.rendertargets[int(rendertarget_enum.value)] = rendertarget

    def create_rendertargets(self, width, height):
        self.clear()

        fullsize_x = width
        fullsize_y = height
        halfsize_x = int(width / 2)
        halfsize_y = int(height / 2)

        self.create_rendertarget(RenderTargets.BACKBUFFER,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE)

        self.create_rendertarget(RenderTargets.WORLD_NORMAL,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE)

        self.create_rendertarget(RenderTargets.DEPTHSTENCIL,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_DEPTH24_STENCIL8,
                                 texture_format=GL_DEPTH_STENCIL,
                                 data_type=GL_UNSIGNED_INT_24_8,
                                 min_filter=GL_NEAREST,
                                 mag_filter=GL_NEAREST,
                                 enable_mipmap=False)

        self.create_rendertarget(RenderTargets.DIFFUSE,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE)

        self.create_rendertarget(RenderTargets.SHADOWMAP,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_DEPTH_COMPONENT32,
                                 texture_format=GL_DEPTH_COMPONENT,
                                 data_type=GL_FLOAT,
                                 min_filter=GL_NEAREST,
                                 mag_filter=GL_NEAREST,
                                 enable_mipmap=False)
