import copy

import numpy as np

from OpenGL.GL import *

from PyEngine3D.Utilities import *
from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.OpenGLContext import TextureCube, CreateTexture
from .RenderTarget import RenderTargets
from .Actor import StaticActor
from .Camera import Camera


class LightProbe(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)

        self.isRendered = False

        if CoreManager.instance().is_basic_mode:
            self.texture_probe = None
        else:
            self.texture_probe = self.generate_texture_probe(self.name)

    def get_save_data(self):
        save_data = StaticActor.get_save_data(self)
        return save_data

    def delete(self):
        if self.texture_probe is not None:
            self.texture_probe.delete()
            self.texture_probe = None

    def replace_texture_probe(self, texture_probe):
        self.delete()
        self.texture_probe = texture_probe

    @staticmethod
    def generate_texture_probe(name):
        texture_datas = RenderTargets.LIGHT_PROBE_ATMOSPHERE.get_texture_info()
        return CreateTexture(name=name, **texture_datas)
