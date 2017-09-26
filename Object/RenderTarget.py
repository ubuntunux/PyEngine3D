from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from Utilities import Singleton, GetClassName, Attributes, AutoEnum
from Common import logger
from OpenGLContext import Texture2D, Texture2DMultiSample, TextureCube, RenderBuffer


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
        self.renderer = None
        self.rendertargets = []
        self.temp_rendertargets = dict()

    def initialize(self, core_manager):
        logger.info("initialize " + GetClassName(self))
        self.core_manager = core_manager
        self.renderer = core_manager.renderer
        self.clear()

    def clear(self):
        self.rendertargets = [None, ] * RenderTargets.COUNT.value
        self.temp_rendertargets = {}

    def find_rendertarget(self, rendertarget_index, rendertarget_name):
        if rendertarget_index < len(self.rendertargets):
            return self.rendertargets[rendertarget_index]
        elif rendertarget_name in self.temp_rendertargets:
            return self.temp_rendertargets[rendertarget_name]
        return None

    def get_rendertarget(self, texture_enum: RenderTargets):
        return self.rendertargets[texture_enum.value]

    def get_temporary(self, rendertarget_name, reference_rendertarget=None, scale=1.0):
        temp_rendertarget = None
        if rendertarget_name in self.temp_rendertargets:
            temp_rendertarget = self.temp_rendertargets[rendertarget_name]
        elif reference_rendertarget:
            rendertarget_datas = reference_rendertarget.get_save_data()
            rendertarget_datas['width'] = int(rendertarget_datas['width'] * scale)
            rendertarget_datas['height'] = int(rendertarget_datas['height'] * scale)
            if 'data' in rendertarget_datas:
                rendertarget_datas.pop('data')
            rendertarget_type = rendertarget_datas['texture_type']
            temp_rendertarget = rendertarget_type(name=rendertarget_name, **rendertarget_datas)
            if temp_rendertarget:
                self.temp_rendertargets[rendertarget_name] = temp_rendertarget
                self.core_manager.sendRenderTargetInfo(temp_rendertarget.name)

        if temp_rendertarget is None:
            logger.warn("Failed to get temporary %s render target." % rendertarget_name)
        return temp_rendertarget

    def copy_rendertarget(self, src, dst, filter_type=GL_NEAREST):
        glBindFramebuffer(GL_READ_FRAMEBUFFER, src.buffer)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dst.buffer)
        glBlitFramebuffer(0, 0, src.width, src.height, 0, 0, dst.width, dst.height, GL_COLOR_BUFFER_BIT, filter_type)

    def create_rendertarget(self, rendertarget_enum, rendertarget_type, **kwargs):
        index = int(rendertarget_enum.value)
        rendertarget_name = str(rendertarget_enum)
        if '.' in rendertarget_name:
            rendertarget_name = rendertarget_name.split('.')[-1]
        rendertarget = rendertarget_type(name=rendertarget_name, **kwargs)

        if rendertarget:
            if self.rendertargets[index]:
                # value copy
                object_copy(rendertarget, self.rendertargets[index])
            else:
                self.rendertargets[index] = rendertarget

    def create_rendertargets(self):
        self.clear()

        width = self.renderer.width
        height = self.renderer.height

        msaa_multisamples = self.renderer.postprocess.get_msaa_multisamples()
        msaa_rendertarget = Texture2D if msaa_multisamples < 4 else Texture2DMultiSample

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
                                 min_filter=GL_LINEAR,
                                 mag_filter=GL_LINEAR,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.DEPTHSTENCIL,
                                 rendertarget_type=msaa_rendertarget,
                                 multisamples=msaa_multisamples,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_DEPTH24_STENCIL8,
                                 texture_format=GL_DEPTH_STENCIL,
                                 data_type=GL_UNSIGNED_INT_24_8,
                                 min_filter=GL_LINEAR,
                                 mag_filter=GL_LINEAR,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.HDR,
                                 rendertarget_type=msaa_rendertarget,
                                 multisamples=msaa_multisamples,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA16F,
                                 texture_format=GL_BGRA,
                                 min_filter=GL_LINEAR,
                                 mag_filter=GL_LINEAR,
                                 data_type=GL_FLOAT,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.DIFFUSE,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE,
                                 min_filter=GL_LINEAR,
                                 mag_filter=GL_LINEAR,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.WORLD_NORMAL,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE,
                                 min_filter=GL_LINEAR,
                                 mag_filter=GL_LINEAR,
                                 wrap=GL_CLAMP)

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
                                 data_type=GL_UNSIGNED_BYTE,
                                 min_filter=GL_LINEAR,
                                 mag_filter=GL_LINEAR,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.VELOCITY,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RG32F,
                                 texture_format=GL_RG,
                                 data_type=GL_FLOAT,
                                 min_filter=GL_LINEAR,
                                 mag_filter=GL_LINEAR,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.TEMP_RGBA8,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE,
                                 min_filter=GL_LINEAR,
                                 mag_filter=GL_LINEAR,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.TEMP_HDR,
                                 rendertarget_type=Texture2D,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA16F,
                                 texture_format=GL_BGRA,
                                 data_type=GL_FLOAT,
                                 min_filter=GL_LINEAR,
                                 mag_filter=GL_LINEAR,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.TEMP_MULTISAMPLE_X4,
                                 rendertarget_type=Texture2DMultiSample,
                                 multisamples=4,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 texture_format=GL_BGRA,
                                 data_type=GL_UNSIGNED_BYTE,
                                 min_filter=GL_LINEAR,
                                 mag_filter=GL_LINEAR,
                                 wrap=GL_CLAMP)

        self.create_rendertarget(RenderTargets.TEMP_RENDER_BUFFER_MULTISAMPLE,
                                 rendertarget_type=RenderBuffer,
                                 multisamples=4,
                                 width=fullsize_x,
                                 height=fullsize_y,
                                 internal_format=GL_RGBA8,
                                 wrap=GL_CLAMP)

        self.core_manager.clearRenderTargetList()
        for i in range(RenderTargets.COUNT.value):
            self.core_manager.sendRenderTargetInfo(self.rendertargets[i].name)
