import math

import numpy as np

from OpenGL.GL import *

from PyEngine3D.Utilities import *
from PyEngine3D.Common import logger
from PyEngine3D.OpenGLContext import Texture2D, RenderBuffer, CreateTexture


class Viewport:
    def __init__(self, viewport_name):
        self.name = viewport_name
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.rendertarget = None

    def create(self, x, y, width, height):
        self.delete()

        options = dict(
            texture_type=Texture2D,
            width=width,
            height=height,
            internal_format=GL_RGBA8,
            texture_format=GL_RGBA,
            data_type=GL_UNSIGNED_BYTE,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            wrap=GL_CLAMP
        )

        self.rendertarget = CreateTexture(name=self.name, **options)

        # overwrite pattern
        # object_copy(rendertarget, self.rendertarget)

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
