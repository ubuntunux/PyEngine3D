from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from Utilities import Singleton, GetClassName, Attributes, AutoEnum
from Common import logger
from .Texture import Texture2D


class RenderTargets(AutoEnum):
    BACKBUFFER = ()
    DEPTHSTENCIL = ()
    HDR = ()
    DIFFUSE = ()
    WORLD_NORMAL = ()
    SHADOWMAP = ()
    LINEAR_DEPTH = ()
    SCREEN_SPACE_REFLECTION = ()
    VELOCITY = ()
    TEMP01_GL_RGBA8 = ()
    COUNT = ()


class RenderTargetManager(Singleton):
    name = "RenderTargetManager"

    def __init__(self):
        self.core_manager = None
        self.rendertargets = []
        self.temp_rendertargets = {}

    def initialize(self, core_manager):
        logger.info("initialize " + GetClassName(self))
        self.core_manager = core_manager
        self.clear()

    def clear(self):
        self.rendertargets = [None, ] * RenderTargets.COUNT.value
        self.temp_rendertargets = {}

    def get_rendertarget(self, texture_enum: RenderTargets) -> Texture2D:
        return self.rendertargets[texture_enum.value]

    def get_temporary(self, texture_enum: RenderTargets) -> Texture2D:
        rendertarget = self.rendertargets[texture_enum.value]
        if not rendertarget.using:
            rendertarget.using = True
            return rendertarget
        logger.warn("%s are using." % texture_enum)
        return rendertarget

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
                                 data_type=GL_UNSIGNED_BYTE,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.DEPTHSTENCIL,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_DEPTH24_STENCIL8,
                                 texture_format=GL_DEPTH_STENCIL,
                                 data_type=GL_UNSIGNED_INT_24_8,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.HDR,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA16F,
                                 texture_format=GL_BGRA,
                                 data_type=GL_FLOAT)

        self.create_rendertarget(RenderTargets.DIFFUSE,
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

        # attach to depth render target
        self.create_rendertarget(RenderTargets.SHADOWMAP,
                                 width=4096,
                                 height=4096,
                                 internal_format=GL_DEPTH_COMPONENT32,
                                 texture_format=GL_DEPTH_COMPONENT,
                                 data_type=GL_FLOAT,
                                 min_filter=GL_NEAREST,
                                 mag_filter=GL_NEAREST,
                                 wrap=GL_CLAMP)

        # attach to color render target
        self.create_rendertarget(RenderTargets.LINEAR_DEPTH,
                                 width=fullsize_x,
                                 height=fullsize_x,
                                 internal_format=GL_R32F,
                                 texture_format=GL_RED,
                                 data_type=GL_FLOAT,
                                 min_filter=GL_NEAREST,
                                 mag_filter=GL_NEAREST)

        self.create_rendertarget(RenderTargets.SCREEN_SPACE_REFLECTION,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE)

        self.create_rendertarget(RenderTargets.VELOCITY,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RG32F,
                                 texture_format=GL_RG,
                                 data_type=GL_FLOAT)

        self.create_rendertarget(RenderTargets.TEMP01_GL_RGBA8,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE,
                                 wrap=GL_CLAMP)
