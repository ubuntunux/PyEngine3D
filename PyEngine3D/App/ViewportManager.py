import math

import numpy as np

from PyEngine3D.Utilities import *
from PyEngine3D.Common import logger, COLOR_BLACK


class Viewport:
    def __init__(self, viewport_name):
        self.name = viewport_name
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

    def initialize(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def update(self, dt):
        pass


class ViewportManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.renderer = None
        self.main_viewport = None
        self.viewports = []

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.renderer = core_manager.renderer
        self.main_viewport = self.create_viewport("VIEWPORT_MAIN")

    def clear(self):
        for viewport in self.viewports:
            viewport.delete()

        self.viewports = []
        self.main_viewport = None

    def resize(self, width, height):
        self.main_viewport.initialize(0, 0, width, height)

    def create_viewport(self, viewport_name):
        viewport = Viewport(viewport_name)
        self.viewports.append(viewport)
        return viewport

    def viewport_count(self):
        return len(self.rendertarget)

    def update(self, dt):
        for viewport in self.viewports:
            viewport.update(dt)
