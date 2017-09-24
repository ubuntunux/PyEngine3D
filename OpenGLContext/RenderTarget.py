from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from Utilities import Singleton, GetClassName, Attributes, AutoEnum
from Common import logger
from .Texture import Texture2D, Texture2DMultiSample, TextureCube
from .RenderBuffer import  RenderBuffer


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
    TEMP_RENDER_BUFFER_MULTISAMPLE = ()
    TEMP_RGBA8 = ()
    TEMP_HDR = ()
    TEMP_MULTISAMPLE_X4 = ()
    COUNT = ()


class RenderTargetManager(Singleton):
    name = "RenderTargetManager"

    def __init__(self):
        self.core_manager = None
        self.rendertargets = []
        self.temp_rendertargets = dict()

    def initialize(self, core_manager):
        logger.info("initialize " + GetClassName(self))
        self.core_manager = core_manager
        self.clear()

    def clear(self):
        self.rendertargets = [None, ] * RenderTargets.COUNT.value

    def get_rendertarget(self, texture_enum: RenderTargets):
        return self.rendertargets[texture_enum.value]

    def get_temporary(self, rendertarget_name, reference_rendertarget, scale=1.0):
        if rendertarget_name in self.temp_rendertargets:
            temp_rendertarget = self.temp_rendertargets[rendertarget_name]
        else:
            rendertarget_datas = reference_rendertarget.get_save_data()
            rendertarget_datas['width'] = int(rendertarget_datas['width'] * scale)
            rendertarget_datas['height'] = int(rendertarget_datas['height'] * scale)
            rendertarget_type = rendertarget_datas['texture_type']
            temp_rendertarget = rendertarget_type(name=rendertarget_name, **rendertarget_datas)
            self.temp_rendertargets[rendertarget_name] = temp_rendertarget

        if temp_rendertarget and not temp_rendertarget.using:
            temp_rendertarget.using = True
        else:
            logger.warn("%s is using." % name)
        return temp_rendertarget

    def copy_rendertarget(self, src, dst, filter_type=GL_NEAREST):
        glBindFramebuffer(GL_READ_FRAMEBUFFER, src.buffer)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dst.buffer)
        glBlitFramebuffer(0, 0, src.width, src.height, 0, 0, dst.width, dst.height, GL_COLOR_BUFFER_BIT, filter_type)

    def create_rendertarget(self, rendertarget_enum, rendertarget_type, **kwargs):
        index = int(rendertarget_enum.value)
        rendertarget = rendertarget_type(name=str(rendertarget_enum), **kwargs)

        if self.rendertargets[index]:
            # value copy
            object_copy(rendertarget, self.rendertargets[index])
        else:
            self.rendertargets[index] = rendertarget

    def create_rendertargets(self, width, height):
        self.clear()

        fullsize_x = width
        fullsize_y = height
        halfsize_x = int(width / 2)
        halfsize_y = int(height / 2)

        self.create_rendertarget(RenderTargets.BACKBUFFER,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.DEPTHSTENCIL,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_DEPTH24_STENCIL8,
                                 texture_format=GL_DEPTH_STENCIL,
                                 data_type=GL_UNSIGNED_INT_24_8,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.HDR,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA16F,
                                 texture_format=GL_BGRA,
                                 data_type=GL_FLOAT)

        self.create_rendertarget(RenderTargets.DIFFUSE,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE)

        self.create_rendertarget(RenderTargets.WORLD_NORMAL,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE)

        # attach to depth render target
        self.create_rendertarget(RenderTargets.SHADOWMAP,
                                 rendertarget_type=Texture2D,
                                 width=1024,
                                 height=1024,
                                 internal_format=GL_DEPTH_COMPONENT32,
                                 texture_format=GL_DEPTH_COMPONENT,
                                 data_type=GL_FLOAT,
                                 min_filter=GL_NEAREST,
                                 mag_filter=GL_NEAREST,
                                 wrap=GL_CLAMP)

        # attach to color render target
        self.create_rendertarget(RenderTargets.LINEAR_DEPTH,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_x,
                                 internal_format=GL_R32F,
                                 texture_format=GL_RED,
                                 data_type=GL_FLOAT,
                                 min_filter=GL_NEAREST,
                                 mag_filter=GL_NEAREST)

        self.create_rendertarget(RenderTargets.SCREEN_SPACE_REFLECTION,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE)

        self.create_rendertarget(RenderTargets.VELOCITY,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RG32F,
                                 texture_format=GL_RG,
                                 data_type=GL_FLOAT)

        self.create_rendertarget(RenderTargets.TEMP_RGBA8,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.TEMP_HDR,
                                 rendertarget_type=Texture2D,
                                 multisamples=4,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA16F,
                                 texture_format=GL_BGRA,
                                 data_type=GL_FLOAT)

        self.create_rendertarget(RenderTargets.TEMP_MULTISAMPLE_X4,
                                 rendertarget_type=Texture2DMultiSample,
                                 multisamples=4,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE)

        self.create_rendertarget(RenderTargets.TEMP_RENDER_BUFFER_MULTISAMPLE,
                                 rendertarget_type=RenderBuffer,
                                 multisamples=4,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8)
