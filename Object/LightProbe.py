import copy

import numpy as np

from OpenGL.GL import *

from Utilities import *
from Common import logger
from App import CoreManager
from OpenGLContext import Texture2D, TextureCube, CreateTexture
from .Actor import StaticActor
from .Camera import Camera


class LightProbe(StaticActor):
    texture_datas = dict(
        texture_type=Texture2D,
        width=512,
        height=512,
        internal_format=GL_RGBA16F,
        texture_format=GL_RGBA,
        min_filter=GL_LINEAR_MIPMAP_NEAREST,
        mag_filter=GL_LINEAR,
        data_type=GL_FLOAT,
        wrap=GL_CLAMP_TO_EDGE
    )

    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)

        self.isValid = False

        self.texture_right = None
        self.texture_left = None
        self.texture_top = None
        self.texture_bottom = None
        self.texture_front = None
        self.texture_back = None
        self.texture_probe = None

    def get_save_data(self):
        save_data = StaticActor.get_save_data(self)
        return save_data

    def clear(self):
        self.clear_texture_faces()
        self.texture_probe.clear()
        self.texture_probe = None

    def clear_texture_faces(self):
        if self.texture_right:
            self.texture_right.clear()
            self.texture_right = None
        if self.texture_left:
            self.texture_left.clear()
            self.texture_left = None
        if self.texture_top:
            self.texture_top.clear()
            self.texture_top = None
        if self.texture_bottom:
            self.texture_bottom.clear()
            self.texture_bottom = None
        if self.texture_front:
            self.texture_front.clear()
            self.texture_front = None
        if self.texture_back:
            self.texture_back.clear()
            self.texture_back = None

    def generate_texture_faces(self):
        self.texture_right = CreateTexture(name=self.name + "_right", **self.texture_datas)
        self.texture_left = CreateTexture(name=self.name + "_left", **self.texture_datas)
        self.texture_top = CreateTexture(name=self.name + "_top", **self.texture_datas)
        self.texture_bottom = CreateTexture(name=self.name + "_bottom", **self.texture_datas)
        self.texture_front = CreateTexture(name=self.name + "_front", **self.texture_datas)
        self.texture_back = CreateTexture(name=self.name + "_back", **self.texture_datas)

    def generate_texture_probe(self):
        cube_texture_datas = copy.copy(self.texture_datas)
        cube_texture_datas['texture_type'] = TextureCube
        cube_texture_datas['texture_positive_x'] = self.texture_right
        cube_texture_datas['texture_negative_x'] = self.texture_left
        cube_texture_datas['texture_positive_y'] = self.texture_top
        cube_texture_datas['texture_negative_y'] = self.texture_bottom
        cube_texture_datas['texture_positive_z'] = self.texture_front
        cube_texture_datas['texture_negative_z'] = self.texture_back
        self.texture_probe = CreateTexture(name=self.name + "_cube", **cube_texture_datas)
        # self.clear_texture_faces()

    def get_texture(self, face):
        return getattr(self, "texture_" + face)
