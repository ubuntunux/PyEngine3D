import random

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.Utilities import Attributes
from PyEngine3D.OpenGLContext import CreateTexture, Material, Texture2D, Texture3D, TextureCube


class CloudTexture3D:
    def __init__(self, **data):
        self.name = self.__class__.__name__
        self.texture_name = 'cloud_3d'
        self.width = data.get('width', 128)
        self.height = data.get('height', 128)
        self.depth = data.get('depth', 128)
        self.sphere_scale = data.get('sphere_scale', 0.15)
        self.sphere_count = data.get('sphere_count', 4096)
        self.noise_persistance = data.get('noise_persistance', 0.7)
        self.noise_scale = data.get('noise_scale', 6)
        self.attribute = Attributes()

    def generate_texture(self):
        logger.info("Generate CloudTexture3D.")

        core_manager = CoreManager.getInstance()
        resource_manager = core_manager.resource_manager
        renderer = core_manager.renderer

        texture = CreateTexture(
            name=self.texture_name,
            texture_type=Texture3D,
            width=self.width,
            height=self.height,
            depth=self.depth,
            internal_format=GL_R16F,
            texture_format=GL_RED,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_REPEAT,
        )

        resource = resource_manager.texture_loader.get_resource(self.texture_name)
        if resource is None:
            resource = resource_manager.texture_loader.create_resource(self.texture_name, texture)
            resource_manager.texture_loader.save_resource(resource.name)
        else:
            old_texture = resource.get_data()
            old_texture.delete()
            resource.set_data(texture)

        glPolygonMode(GL_FRONT_AND_BACK, renderer.view_mode)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glFrontFace(GL_CCW)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(True)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        renderer.set_blend_state(False)

        renderer.framebuffer_manager.bind_framebuffer(texture)
        glClear(GL_COLOR_BUFFER_BIT)

        mat = resource_manager.get_material_instance('procedural.cloud_noise_3d')
        mat.use_program()
        mat.bind_uniform_data('texture_random', resource_manager.get_texture("common.random"))
        mat.bind_uniform_data('random_seed', random.random())
        mat.bind_uniform_data('sphere_count', self.sphere_count)
        mat.bind_uniform_data('sphere_scale', self.sphere_scale)
        mat.bind_uniform_data('noise_persistance', self.noise_persistance)
        mat.bind_uniform_data('noise_scale', self.noise_scale)

        for i in range(texture.depth):
            mat.bind_uniform_data('depth', i / texture.depth)
            renderer.framebuffer_manager.bind_framebuffer(texture, target_layer=i)
            renderer.postprocess.draw_elements()

        renderer.restore_blend_state_prev()

    def get_save_data(self):
        save_data = dict(
            texture_type=self.__class__.__name__,
            texture_name=self.texture_name,
            width=self.width,
            height=self.height,
            depth=self.depth,
            sphere_scale=self.sphere_scale,
            sphere_count=self.sphere_count,
            noise_persistance=self.noise_persistance,
            noise_scale=self.noise_scale,
        )
        return save_data

    def get_attribute(self):
        self.attribute.set_attribute("texture_name", self.texture_name)
        self.attribute.set_attribute("width", self.width)
        self.attribute.set_attribute("height", self.height)
        self.attribute.set_attribute("depth", self.depth)
        self.attribute.set_attribute("sphere_scale", self.sphere_scale)
        self.attribute.set_attribute("sphere_count", self.sphere_count)
        self.attribute.set_attribute("noise_persistance", self.noise_persistance)
        self.attribute.set_attribute("noise_scale", self.noise_scale)
        return self.attribute

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        if hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)
        return self.attribute
