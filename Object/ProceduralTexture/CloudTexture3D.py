import random

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from OpenGL.GL import *

from Common import logger
from App import CoreManager
from Utilities import Attributes
from OpenGLContext import CreateTexture, Material, Texture2D, Texture3D, TextureCube


class CloudTexture3D:
    def __init__(self, **data):
        self.name = self.__class__.__name__
        self.texture_name = 'cloud_3d'
        self.width = data.get('width', 256)
        self.height = data.get('height', 256)
        self.depth = data.get('depth', 32)
        self.sphere_scale = data.get('sphere_scale', 0.3)
        self.sphere_count = data.get('sphere_count', 500)
        self.attribute = Attributes()

    def generate_texture(self):
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

        resource = resource_manager.textureLoader.getResource(self.texture_name)
        if resource is None:
            resource = resource_manager.textureLoader.create_resource(self.texture_name, texture)
            resource_manager.textureLoader.save_resource(resource.name)
        else:
            old_texture = resource.get_data()
            old_texture.delete()
            resource.set_data(texture)

        glPolygonMode(GL_FRONT_AND_BACK, renderer.viewMode)
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

        renderer.postprocess.bind_quad()

        mat = resource_manager.getMaterialInstance('procedural.cloud_noise_3d')
        mat.use_program()
        mat.bind_uniform_data('texture_random', resource_manager.getTexture("common.random"))
        mat.bind_uniform_data('random_seed', random.random())
        mat.bind_uniform_data('sphere_count', self.sphere_count)
        mat.bind_uniform_data('sphere_scale', self.sphere_scale)

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
        )
        return save_data

    def getAttribute(self):
        self.attribute.setAttribute("texture_name", self.texture_name)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
        self.attribute.setAttribute("depth", self.depth)
        self.attribute.setAttribute("sphere_scale", self.sphere_scale)
        self.attribute.setAttribute("sphere_count", self.sphere_count)
        return self.attribute

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)
        return self.attribute
