import math
import random

import numpy as np

from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from Utilities import *
from Common import logger
from OpenGLContext import Texture2D, Texture2DArray, Texture2DMultiSample, TextureCube, RenderBuffer, CreateTexture
from Object.Ocean import Constants as OceanConstants


class Option:
    NONE = 0
    MSAA = 1 << 1
    SSAA = 1 << 2


class RenderTargets:
    BACKBUFFER = None
    DEPTHSTENCIL = None
    HDR = None
    HDR_PREV = None
    LIGHT_PROBE_ATMOSPHERE = None
    TAA_RESOLVE = None
    DIFFUSE = None
    MATERIAL = None
    WORLD_NORMAL = None
    SHADOWMAP = None
    LINEAR_DEPTH = None
    SCREEN_SPACE_REFLECTION = None
    SSAO = None
    VELOCITY = None
    FFT_A = None
    FFT_B = None
    TEMP_RENDER_BUFFER_MULTISAMPLE = None
    TEMP_RGBA8 = None
    TEMP_2D_ARRAY = None
    TEMP_MULTISAMPLE_X4 = None


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
                self.core_manager.sendRenderTargetInfo(temp_rendertarget.name)

        if temp_rendertarget is None:
            logger.warn("Failed to get temporary %s render target." % rendertarget_name)
        return temp_rendertarget

    def create_rendertarget(self, rendertarget_name, **kwargs):
        datas = Data(**kwargs)
        option = datas.option or Option.NONE

        rendertarget_type = kwargs.get('texture_type', Texture2D)

        if (Option.MSAA & option) and self.renderer.postprocess.enable_MSAA():
            if rendertarget_type == Texture2D:
                rendertarget_type = Texture2DMultiSample
            datas.multisample_count = self.renderer.postprocess.get_msaa_multisample_count()
        elif (Option.SSAA & option) and self.renderer.postprocess.is_SSAA():
            datas.width *= 2
            datas.height *= 2

        # Create RenderTarget
        if rendertarget_type == RenderBuffer:
            rendertarget = RenderBuffer(rendertarget_name, datas=datas)
        else:
            rendertarget = CreateTexture(name=rendertarget_name, **datas.get_dict())

        if rendertarget:
            if rendertarget_name not in self.rendertargets:
                self.rendertargets[rendertarget_name] = rendertarget
                # send rendertarget info to GUI
                self.core_manager.sendRenderTargetInfo(rendertarget_name)
            else:
                # overwrite
                self.rendertargets[rendertarget_name].delete()
                object_copy(rendertarget, self.rendertargets[rendertarget_name])
        else:
            logger.error("Failed to crate a render target. %s" % rendertarget_name)
        return rendertarget

    def recreate_rendertargets(self):
        self.core_manager.clearRenderTargetList()

        for rendertarget_name in self.rendertargets:
            rendertarget = self.rendertargets[rendertarget_name]
            datas = rendertarget.get_texture_info()
            self.create_rendertarget(rendertarget_name, **datas)
            self.core_manager.sendRenderTargetInfo(rendertarget_name)

        self.clear_temp_rendertargets()
        self.core_manager.gc_collect()

    def create_rendertargets(self):
        self.clear()

        # Note : # clear rendertarget infos in GUI
        self.core_manager.clearRenderTargetList()

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

        RenderTargets.HDR = self.create_rendertarget(
            "HDR",
            texture_type=Texture2D,
            option=Option.MSAA | Option.SSAA,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=hdr_internal_format,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=hdr_data_type,
            wrap=GL_CLAMP
        )

        RenderTargets.HDR_PREV = self.create_rendertarget(
            "HDR_Prev",
            texture_type=Texture2D,
            option=Option.MSAA | Option.SSAA,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=hdr_internal_format,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=hdr_data_type,
            wrap=GL_CLAMP
        )

        RenderTargets.LIGHT_PROBE_ATMOSPHERE = self.create_rendertarget(
            "LIGHT_PROBE_ATMOSPHERE",
            texture_type=TextureCube,
            width=512,
            height=512,
            internal_format=hdr_internal_format,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR_MIPMAP_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=hdr_data_type,
            wrap=GL_REPEAT
        )

        RenderTargets.TAA_RESOLVE = self.create_rendertarget(
            "TAA Resolve",
            texture_type=Texture2D,
            option=Option.MSAA | Option.SSAA,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=hdr_internal_format,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=hdr_data_type,
            wrap=GL_CLAMP
        )

        RenderTargets.DIFFUSE = self.create_rendertarget(
            "DIFFUSE",
            texture_type=Texture2D,
            option=Option.SSAA,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            data_type=GL_UNSIGNED_BYTE,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

        RenderTargets.MATERIAL = self.create_rendertarget(
            "MATERIAL",
            texture_type=Texture2D,
            option=Option.SSAA,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            data_type=GL_UNSIGNED_BYTE,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP
        )

        RenderTargets.WORLD_NORMAL = self.create_rendertarget(
            "WORLD_NORMAL",
            texture_type=Texture2D,
            option=Option.SSAA,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            data_type=GL_UNSIGNED_BYTE,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP
        )

        # It must attach to depth render target
        RenderTargets.SHADOWMAP = self.create_rendertarget(
            "SHADOWMAP",
            texture_type=Texture2D,
            width=1024,
            height=1024,
            internal_format=GL_DEPTH_COMPONENT32,
            texture_format=GL_DEPTH_COMPONENT,
            data_type=GL_FLOAT,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

        # It must attach to color render target
        RenderTargets.LINEAR_DEPTH = self.create_rendertarget(
            "LINEAR_DEPTH",
            texture_type=Texture2D,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=GL_R32F,
            texture_format=GL_RED,
            data_type=GL_FLOAT,
            min_filter=GL_LINEAR_MIPMAP_NEAREST,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

        RenderTargets.SCREEN_SPACE_REFLECTION = self.create_rendertarget(
            "SCREEN_SPACE_REFLECTION",
            texture_type=Texture2D,
            width=halfsize_x,
            height=halfsize_y,
            internal_format=hdr_internal_format,
            texture_format=GL_RGBA,
            data_type=hdr_data_type,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

        RenderTargets.SSAO = self.create_rendertarget(
            "SSAO",
            texture_type=Texture2D,
            width=halfsize_x,
            height=halfsize_y,
            internal_format=GL_R16F,
            texture_format=GL_RED,
            data_type=GL_FLOAT,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

        RenderTargets.VELOCITY = self.create_rendertarget(
            "VELOCITY",
            texture_type=Texture2D,
            option=Option.SSAA,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=GL_RG32F,
            texture_format=GL_RG,
            data_type=GL_FLOAT,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP
        )

        RenderTargets.FFT_A = self.create_rendertarget(
            'FFT_A',
            texture_type=Texture2DArray,
            image_mode='RGBA',
            width=OceanConstants.FFT_SIZE,
            height=OceanConstants.FFT_SIZE,
            depth=5,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR_MIPMAP_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_REPEAT
        )

        RenderTargets.FFT_B = self.create_rendertarget(
            'FFT_B',
            texture_type=Texture2DArray,
            image_mode='RGBA',
            width=OceanConstants.FFT_SIZE,
            height=OceanConstants.FFT_SIZE,
            depth=5,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR_MIPMAP_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_REPEAT
        )

        RenderTargets.TEMP_RGBA8 = self.create_rendertarget(
            "TEMP_RGBA8",
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

        RenderTargets.TEMP_2D_ARRAY = self.create_rendertarget(
            "TEMP_2D_ARRAY",
            texture_type=Texture2DArray,
            width=fullsize_x,
            height=fullsize_y,
            depth=5,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            data_type=GL_UNSIGNED_BYTE,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

        RenderTargets.TEMP_MULTISAMPLE_X4 = self.create_rendertarget(
            "TEMP_MULTISAMPLE_X4",
            texture_type=Texture2DMultiSample,
            multisample_count=4,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            data_type=GL_UNSIGNED_BYTE,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

        RenderTargets.TEMP_RENDER_BUFFER_MULTISAMPLE = self.create_rendertarget(
            "TEMP_RENDER_BUFFER_MULTISAMPLE",
            texture_type=RenderBuffer,
            multisample_count=4,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=GL_RGBA8,
            wrap=GL_CLAMP
        )

        self.texture_lod_in_ssao = math.log2(RenderTargets.LINEAR_DEPTH.width) - math.log2(RenderTargets.SSAO.width)

        self.core_manager.gc_collect()
