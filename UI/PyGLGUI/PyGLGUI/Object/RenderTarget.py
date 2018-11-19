from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from ..Utilities import *
from ..Common import logger
from ..OpenGLContext import Texture2D, Texture2DArray, Texture2DMultiSample, TextureCube, RenderBuffer, CreateTexture


class Option:
    NONE = 0
    MSAA = 1 << 1
    SSAA = 1 << 2


class RenderTargets:
    BACKBUFFER = None
    DEPTHSTENCIL = None


class RenderTargetManager(Singleton):
    name = "RenderTargetManager"

    def __init__(self):
        self.core_manager = None
        self.renderer = None
        self.rendertargets = dict()
        self.temp_rendertargets = dict()
        self.first_time = True
        self.texture_lod_in_ssao = 1.0

    def initialize(self, core_manager):
        logger.info("initialize " + GetClassName(self))
        self.core_manager = core_manager
        self.renderer = core_manager.renderer
        self.clear()

    def clear(self):
        self.clear_rendertargets()
        self.clear_temp_rendertargets()

    def clear_rendertargets(self):
        for key, rendertarget in self.rendertargets.items():
            rendertarget.delete()
        self.rendertargets = dict()
        self.core_manager.gc_collect()

    def clear_temp_rendertargets(self):
        for key, rendertarget in self.temp_rendertargets.items():
            rendertarget.delete()
        self.temp_rendertargets = dict()
        self.core_manager.gc_collect()

    def find_rendertarget(self, rendertarget_index, rendertarget_name):
        if rendertarget_index < len(self.rendertargets) and rendertarget_name in self.rendertargets:
            return self.rendertargets[rendertarget_name]
        elif rendertarget_name in self.temp_rendertargets:
            return self.temp_rendertargets[rendertarget_name]
        return None

    def get_rendertarget(self, rendertarget_name):
        return self.rendertargets[rendertarget_name] if rendertarget_name in self.rendertargets else None

    def get_temporary(self, rendertarget_name, reference_rendertarget=None, scale=1.0):
        temp_rendertarget = None
        if rendertarget_name in self.temp_rendertargets:
            temp_rendertarget = self.temp_rendertargets[rendertarget_name]
        elif reference_rendertarget:
            rendertarget_datas = reference_rendertarget.get_texture_info()
            rendertarget_datas['width'] = int(rendertarget_datas['width'] * scale)
            rendertarget_datas['height'] = int(rendertarget_datas['height'] * scale)
            rendertarget_type = rendertarget_datas['texture_type']
            if type(rendertarget_type) is str:
                rendertarget_type = eval(rendertarget_type)
            temp_rendertarget = rendertarget_type(name=rendertarget_name, **rendertarget_datas)
            if temp_rendertarget:
                self.temp_rendertargets[rendertarget_name] = temp_rendertarget
                # send rendertarget info to GUI
                self.core_manager.send_render_target_info(temp_rendertarget.name)

        if temp_rendertarget is None:
            logger.warn("Failed to get temporary %s render target." % rendertarget_name)
        return temp_rendertarget

    def create_rendertarget(self, rendertarget_name, **kwargs):
        datas = Data(**kwargs)
        option = datas.option or Option.NONE

        rendertarget_type = kwargs.get('texture_type', Texture2D)

        # Create RenderTarget
        if rendertarget_type == RenderBuffer:
            rendertarget = RenderBuffer(rendertarget_name, datas=datas)
        else:
            rendertarget = CreateTexture(name=rendertarget_name, **datas.get_dict())

        if rendertarget:
            if rendertarget_name not in self.rendertargets:
                self.rendertargets[rendertarget_name] = rendertarget
            else:
                # overwrite
                self.rendertargets[rendertarget_name].delete()
                object_copy(rendertarget, self.rendertargets[rendertarget_name])
        else:
            logger.error("Failed to crate a render target. %s" % rendertarget_name)
        return rendertarget

    def recreate_rendertargets(self):
        for rendertarget_name in self.rendertargets:
            rendertarget = self.rendertargets[rendertarget_name]
            datas = rendertarget.get_texture_info()
            self.create_rendertarget(rendertarget_name, **datas)

        self.clear_temp_rendertargets()
        self.core_manager.gc_collect()

    def create_rendertargets(self):
        self.clear()

        width = self.renderer.width
        height = self.renderer.height

        fullsize_x = width
        fullsize_y = height
        halfsize_x = int(width / 2)
        halfsize_y = int(height / 2)
        quatersize_x = int(width / 4)
        quatersize_y = int(height / 4)

        hdr_internal_format = GL_RGBA16F
        hdr_data_type = GL_FLOAT

        COLOR_BLACK = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
        COLOR_BLACK_NO_ALPHA = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        COLOR_WHITE = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
        COLOR_WHITE_NO_ALPHA = np.array([1.0, 1.0, 1.0, 0.0], dtype=np.float32)

        RenderTargets.BACKBUFFER = self.create_rendertarget(
            "BACKBUFFER",
            texture_type=Texture2D,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            data_type=GL_UNSIGNED_BYTE,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

        RenderTargets.DEPTHSTENCIL = self.create_rendertarget(
            "DEPTHSTENCIL",
            texture_type=Texture2D,
            option=Option.SSAA,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=GL_DEPTH24_STENCIL8,
            texture_format=GL_DEPTH_STENCIL,
            data_type=GL_UNSIGNED_INT_24_8,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP
        )

        self.core_manager.gc_collect()
