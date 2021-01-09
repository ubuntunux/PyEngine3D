import math
import random

import numpy as np

from OpenGL.GL import *
from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

from PyEngine3D.Utilities import *
from PyEngine3D.Common import logger, COLOR_BLACK
from PyEngine3D.OpenGLContext import Texture2D, Texture2DArray, Texture2DMultiSample, TextureCube, RenderBuffer, CreateTexture
from .Ocean import Constants as OceanConstants


class Option:
    NONE = 0
    MSAA = 1 << 1
    SSAA = 1 << 2


class RenderTargets:
    SCREENBUFFER = None
    BACKBUFFER = None
    DEPTH = None
    DEPTH_STENCIL = None
    OBJECT_ID = None
    OBJECT_ID_DEPTH = None
    HDR = None
    HDR_TEMP = None
    HDR_BACKUP = None
    BLOOM_0 = None
    BLOOM_1 = None
    BLOOM_2 = None
    BLOOM_3 = None
    BLOOM_4 = None
    LIGHT_SHAFT = None
    LIGHT_PROBE_ATMOSPHERE = None
    ATMOSPHERE = None
    ATMOSPHERE_INSCATTER = None
    TAA_RESOLVE = None
    DIFFUSE = None
    MATERIAL = None
    WORLD_NORMAL = None
    STATIC_SHADOWMAP = None
    DYNAMIC_SHADOWMAP = None
    COMPOSITE_SHADOWMAP = None
    LINEAR_DEPTH = None
    FOCUS_DISTANCE = None
    SCREEN_SPACE_REFLECTION = None
    SCREEN_SPACE_REFLECTION_RESOLVED_PREV = None
    SCREEN_SPACE_REFLECTION_RESOLVED = None
    SSAO = None
    VELOCITY = None
    FFT_A = None
    FFT_B = None
    TEMP_RENDER_BUFFER_MULTISAMPLE = None
    TEMP_RGBA8 = None
    TEMP_2D_ARRAY = None
    TEMP_MULTISAMPLE_X4 = None
    TEMP_HEIGHT_MAP = None


class RenderTargetManager(Singleton):
    name = "RenderTargetManager"

    def __init__(self):
        self.core_manager = None
        self.viewport_manager = None
        self.renderer = None
        self.rendertargets = dict()
        self.immutable_rendertarget_names = []
        self.temp_rendertargets = dict()
        self.first_time = True
        self.texture_lod_in_ssao = 1.0

    def initialize(self, core_manager):
        logger.info("initialize " + GetClassName(self))
        self.core_manager = core_manager
        self.viewport_manager = core_manager.viewport_manager
        self.renderer = core_manager.renderer
        self.clear()

    def clear(self, force=False):
        self.clear_rendertargets(force)
        self.clear_temp_rendertargets()

    def clear_rendertargets(self, force=False):
        delete_list = []

        for key, rendertarget in self.rendertargets.items():
            if force or key not in self.immutable_rendertarget_names:
                rendertarget.delete()
                delete_list.append(key)

        for key in delete_list:
            self.rendertargets.pop(key)

            if key in self.immutable_rendertarget_names:
                self.immutable_rendertarget_names.pop(key)

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

    def create_rendertarget(self, rendertarget_name, **datas):
        option = datas.get('option', Option.NONE)

        rendertarget_type = datas.get('texture_type', Texture2D)

        if (Option.MSAA & option) and self.renderer.postprocess.enable_MSAA():
            if rendertarget_type == Texture2D:
                rendertarget_type = Texture2DMultiSample
            datas['multisample_count'] = self.renderer.postprocess.get_msaa_multisample_count()
        elif (Option.SSAA & option) and self.renderer.postprocess.is_SSAA():
            datas['width'] = datas.get('width', 1) * 2
            datas['height'] = datas.get('height', 1) * 2

        immutable = datas.get('immutable', False)

        rendertarget = None

        if rendertarget_name in self.rendertargets:
            rendertarget = self.rendertargets[rendertarget_name]

        if not immutable or rendertarget_name not in self.rendertargets:
            # Create RenderTarget
            if rendertarget_type == RenderBuffer:
                rendertarget = RenderBuffer(name=rendertarget_name, **datas)
            else:
                rendertarget = CreateTexture(name=rendertarget_name, **datas)

            if rendertarget_name not in self.rendertargets:
                self.rendertargets[rendertarget_name] = rendertarget

                if immutable:
                    self.immutable_rendertarget_names.append(rendertarget_name)

        # send rendertarget info to GUI
        self.core_manager.send_render_target_info(rendertarget_name)

        if rendertarget is None:
            logger.error("Failed to crate a render target. %s" % rendertarget_name)

        return rendertarget

    def create_rendertargets(self):
        self.clear()

        # Note : # clear rendertarget infos in GUI
        self.core_manager.clear_render_target_list()

        screen_width = self.viewport_manager.root.width
        screen_height = self.viewport_manager.root.height
        width = self.viewport_manager.main_viewport.width
        height = self.viewport_manager.main_viewport.height

        fullsize_x = width
        fullsize_y = height
        halfsize_x = int(width / 2)
        halfsize_y = int(height / 2)
        quatersize_x = int(width / 4)
        quatersize_y = int(height / 4)

        hdr_internal_format = GL_RGBA16F
        hdr_data_type = GL_FLOAT

        RenderTargets.SCREENBUFFER = self.create_rendertarget(
            "SCREENBUFFER",
            texture_type=Texture2D,
            width=screen_width,
            height=screen_height,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            data_type=GL_UNSIGNED_BYTE,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

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

        # NOTE : bind render target
        self.viewport_manager.main_viewport.bind_texture(RenderTargets.BACKBUFFER)

        RenderTargets.DEPTH = self.create_rendertarget(
            "DEPTH",
            texture_type=Texture2D,
            option=Option.SSAA,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=GL_DEPTH_COMPONENT32F,
            texture_format=GL_DEPTH_COMPONENT,
            data_type=GL_FLOAT,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP
        )

        # RenderTargets.DEPTH_STENCIL = self.create_rendertarget(
        #     "DEPTH_STENCIL",
        #     texture_type=Texture2D,
        #     option=Option.SSAA,
        #     width=fullsize_x,
        #     height=fullsize_y,
        #     internal_format=GL_DEPTH24_STENCIL8,
        #     texture_format=GL_DEPTH_STENCIL,
        #     data_type=GL_UNSIGNED_INT_24_8,
        #     min_filter=GL_NEAREST,
        #     mag_filter=GL_NEAREST,
        #     wrap=GL_CLAMP
        # )

        object_id_size = 512

        RenderTargets.OBJECT_ID = self.create_rendertarget(
            "OBJECT_ID",
            texture_type=Texture2D,
            option=Option.NONE,
            width=object_id_size,
            height=object_id_size,
            internal_format=GL_R32F,
            texture_format=GL_RED,
            data_type=GL_FLOAT,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP
        )

        RenderTargets.OBJECT_ID_DEPTH = self.create_rendertarget(
            "OBJECT_ID_DEPTH",
            texture_type=Texture2D,
            option=Option.NONE,
            width=object_id_size,
            height=object_id_size,
            internal_format=GL_DEPTH_COMPONENT32F,
            texture_format=GL_DEPTH_COMPONENT,
            data_type=GL_FLOAT,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP
        )

        hdr_options = dict(
            texture_type=Texture2D,
            option=Option.MSAA | Option.SSAA,
            width=fullsize_x,
            height=fullsize_y,
            internal_format=hdr_internal_format,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR_MIPMAP_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=hdr_data_type,
            clear_color=COLOR_BLACK,
            wrap=GL_CLAMP
        )

        RenderTargets.HDR = self.create_rendertarget("HDR", **hdr_options)
        RenderTargets.HDR_TEMP = self.create_rendertarget("HDR_TEMP", **hdr_options)
        RenderTargets.HDR_BACKUP = self.create_rendertarget("HDR_BACKUP", **hdr_options)

        bloom_options = dict(
            texture_type=Texture2D,
            option=Option.SSAA,
            internal_format=hdr_internal_format,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=hdr_data_type,
            wrap=GL_CLAMP
        )

        RenderTargets.BLOOM_0 = self.create_rendertarget(
            "BLOOM_0",
            width=fullsize_x / 2,
            height=fullsize_y / 2,
            **bloom_options
        )

        RenderTargets.BLOOM_1 = self.create_rendertarget(
            "BLOOM_1",
            width=fullsize_x / 4,
            height=fullsize_y / 4,
            **bloom_options
        )

        RenderTargets.BLOOM_2 = self.create_rendertarget(
            "BLOOM_2",
            width=fullsize_x / 8,
            height=fullsize_y / 8,
            **bloom_options
        )

        RenderTargets.BLOOM_3 = self.create_rendertarget(
            "BLOOM_3",
            width=fullsize_x / 16,
            height=fullsize_y / 16,
            **bloom_options
        )

        RenderTargets.BLOOM_4 = self.create_rendertarget(
            "BLOOM_4",
            width=fullsize_x / 32,
            height=fullsize_y / 32,
            **bloom_options
        )

        RenderTargets.LIGHT_SHAFT = self.create_rendertarget(
            "LIGHT_SHAFT",
            texture_type=Texture2D,
            width=halfsize_x,
            height=halfsize_y,
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
            wrap=GL_CLAMP_TO_EDGE,
            immutable=True
        )

        RenderTargets.ATMOSPHERE = self.create_rendertarget(
            "ATMOSPHERE",
            texture_type=Texture2D,
            width=quatersize_x,
            height=quatersize_y,
            internal_format=hdr_internal_format,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=hdr_data_type,
            wrap=GL_CLAMP_TO_EDGE,
            immutable=True
        )

        RenderTargets.ATMOSPHERE_INSCATTER = self.create_rendertarget(
            "ATMOSPHERE_INSCATTER",
            texture_type=Texture2D,
            width=quatersize_x,
            height=quatersize_y,
            internal_format=hdr_internal_format,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=hdr_data_type,
            wrap=GL_CLAMP_TO_EDGE,
            immutable=True
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
        shadow_map_size = 2048
        RenderTargets.STATIC_SHADOWMAP = self.create_rendertarget(
            "STATIC_SHADOWMAP",
            texture_type=Texture2D,
            width=shadow_map_size,
            height=shadow_map_size,
            internal_format=GL_DEPTH_COMPONENT32,
            texture_format=GL_DEPTH_COMPONENT,
            data_type=GL_FLOAT,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP
        )

        RenderTargets.DYNAMIC_SHADOWMAP = self.create_rendertarget(
            "DYNAMIC_SHADOWMAP",
            texture_type=Texture2D,
            width=shadow_map_size,
            height=shadow_map_size,
            internal_format=GL_DEPTH_COMPONENT32,
            texture_format=GL_DEPTH_COMPONENT,
            data_type=GL_FLOAT,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP
        )

        RenderTargets.COMPOSITE_SHADOWMAP = self.create_rendertarget(
            "COMPOSITE_SHADOWMAP",
            texture_type=Texture2D,
            width=shadow_map_size,
            height=shadow_map_size,
            internal_format=GL_R32F,
            texture_format=GL_RED,
            data_type=GL_FLOAT,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
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
            min_filter=GL_NEAREST_MIPMAP_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP
        )

        data = np.zeros(1, dtype=np.float32)
        RenderTargets.FOCUS_DISTANCE = self.create_rendertarget(
            "FOCUS_DISTANCE",
            texture_type=Texture2D,
            width=1,
            height=1,
            internal_format=GL_R32F,
            texture_format=GL_RED,
            data_type=GL_FLOAT,
            min_filter=GL_NEAREST,
            mag_filter=GL_NEAREST,
            wrap=GL_CLAMP,
            data=data
        )

        ssr_options = dict(
            texture_type=Texture2D,
            width=halfsize_x,
            height=halfsize_y,
            internal_format=hdr_internal_format,
            texture_format=GL_RGBA,
            data_type=hdr_data_type,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            clear_color=COLOR_BLACK,
            wrap=GL_CLAMP
        )

        RenderTargets.SCREEN_SPACE_REFLECTION = self.create_rendertarget("SCREEN_SPACE_REFLECTION", **ssr_options)
        RenderTargets.SCREEN_SPACE_REFLECTION_RESOLVED_PREV = self.create_rendertarget("SCREEN_SPACE_REFLECTION_RESOLVED_PREV", **ssr_options)
        RenderTargets.SCREEN_SPACE_REFLECTION_RESOLVED = self.create_rendertarget("SCREEN_SPACE_REFLECTION_RESOLVED", **ssr_options)

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
            wrap=GL_REPEAT,
            immutable=True
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
            wrap=GL_REPEAT,
            immutable=True
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

        RenderTargets.TEMP_HEIGHT_MAP = self.create_rendertarget(
            "TEMP_HEIGHT_MAP",
            texture_type=Texture2D,
            width=1024,
            height=1024,
            internal_format=GL_R32F,
            texture_format=GL_RED,
            data_type=GL_FLOAT,
            min_filter=GL_LINEAR_MIPMAP_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

        self.texture_lod_in_ssao = math.log2(RenderTargets.LINEAR_DEPTH.width) - math.log2(RenderTargets.SSAO.width)

        self.core_manager.gc_collect()
