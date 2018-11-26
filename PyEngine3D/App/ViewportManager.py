import math

import numpy as np

from OpenGL.GL import *

from PyEngine3D.Utilities import *
from PyEngine3D.Common import logger, COLOR_BLACK
from PyEngine3D.OpenGLContext import Texture2D, RenderBuffer


class Viewport:
    def __init__(self, viewport_name):
        self.name = viewport_name
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.rendertarget = None

    @staticmethod
    def get_options(width, height):
        return dict(
            width=width,
            height=height,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            data_type=GL_UNSIGNED_BYTE,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            clear_color=COLOR_BLACK,
            wrap=GL_CLAMP
        )

    def create(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        options = self.get_options(width, height)

        if self.rendertarget is None:
            self.rendertarget = Texture2D(name=self.name, **options)
        else:
            self.rendertarget.create_texture(**options)

    def delete(self):
        if self.rendertarget is not None:
            self.rendertarget.delete()


class ViewportManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.renderer = None
        self.main_viewport = None
        self.viewports = []

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.renderer = core_manager.renderer
        self.main_viewport = Viewport("VIEWPORT_MAIN")
        self.viewports.append(self.main_viewport)

    def clear(self):
        for viewport in self.viewports:
            viewport.delete()

        self.viewports = []
        self.main_viewport = None

    def resize(self, width, height):
        self.main_viewport.create(0, 0, width, height)

    def split_viewport(self, x, y, width, height):
        pass

    def merge_viewport(self, x, y, width, height):
        pass

    def viewport_count(self):
        return len(self.rendertarget)
