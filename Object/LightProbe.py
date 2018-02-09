import copy

import numpy as np

from OpenGL.GL import *

from Utilities import *
from Common import logger
from App import CoreManager
from OpenGLContext import TextureCube, CreateTexture
from .RenderTarget import RenderTargets
from .Actor import StaticActor
from .Camera import Camera


class LightProbe(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)

        self.isRendered = False
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
        texture_datas = copy.copy(RenderTargets.LIGHT_PROBE_TEMP.get_texture_info())
        texture_datas['texture_type'] = TextureCube
        return CreateTexture(name=name, **texture_datas)
