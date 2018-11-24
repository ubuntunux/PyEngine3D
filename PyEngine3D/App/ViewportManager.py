import math

import numpy as np

from OpenGL.GL import *

from PyEngine3D.Utilities import *
from PyEngine3D.Common import logger
from PyEngine3D.OpenGLContext import Texture2D, RenderBuffer, CreateTexture


class Viewport:
    def __init__(self):
        self.rendertarget = None


class ViewportManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.renderer = None
        self.viewports = []

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.renderer = core_manager.renderer

        # rendertarget = CreateTexture(name=rendertarget_name, **datas.get_dict())
        # RenderTargets.BACKBUFFER = self.create_rendertarget(
        #     "BACKBUFFER",
        #     texture_type=Texture2D,
        #     width=fullsize_x,
        #     height=fullsize_y,
        #     internal_format=GL_RGBA8,
        #     texture_format=GL_RGBA,
        #     data_type=GL_UNSIGNED_BYTE,
        #     min_filter=GL_LINEAR,
        #     mag_filter=GL_LINEAR,
        #     wrap=GL_CLAMP
        # )

    def split_viewport(self, x, y, width, height):
        pass

    def merge_viewport(self, x, y, width, height):
        pass

    def viewport_count(self):
        return len(self.rendertarget)
