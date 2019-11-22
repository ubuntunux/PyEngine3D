import random

import numpy as np
from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.Utilities import Attributes
from PyEngine3D.OpenGLContext import CreateTexture, Texture3D


class VectorFieldTexture3D:
    def __init__(self, **data):
        self.name = self.__class__.__name__
        self.texture_name = 'vector_field_3d'
        self.texture_width = data.get('texture_width', 256)
        self.texture_height = data.get('texture_height', 256)
        self.texture_depth = data.get('texture_depth', 256)
        self.attribute = Attributes()

    def generate_texture(self):
        logger.info("Generate VectorFieldTexture3D.")

        core_manager = CoreManager.getInstance()
        resource_manager = core_manager.resource_manager
        renderer = core_manager.renderer

        texture = CreateTexture(
            name=self.texture_name,
            texture_type=Texture3D,
            width=self.texture_width,
            height=self.texture_height,
            depth=self.texture_depth,
            internal_format=GL_RGBA16F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_CLAMP,
        )

        resource = resource_manager.texture_loader.get_resource(self.texture_name)
        if resource is None:
            resource = resource_manager.texture_loader.create_resource(self.texture_name, texture)
        else:
            old_texture = resource.get_data()
            if old_texture is not None:
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

        material_instance = resource_manager.get_material_instance('procedural.vector_field_3d')
        material_instance.use_program()

        for i in range(texture.depth):
            material_instance.bind_uniform_data('depth', i / texture.depth)
            renderer.framebuffer_manager.bind_framebuffer(texture, target_layer=i)
            renderer.postprocess.draw_elements()

        renderer.restore_blend_state_prev()

        # save
        resource_manager.texture_loader.save_resource(resource.name)

    def get_save_data(self):
        save_data = dict(
            texture_type=self.__class__.__name__,
            texture_name=self.texture_name,
            texture_width=self.texture_width,
            texture_height=self.texture_height,
            texture_depth=self.texture_depth,
        )
        return save_data

    def get_attribute(self):
        self.attribute.set_attribute("texture_name", self.texture_name)
        self.attribute.set_attribute("texture_width", self.texture_width)
        self.attribute.set_attribute("texture_height", self.texture_height)
        self.attribute.set_attribute("texture_depth", self.texture_depth)
        return self.attribute

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        if hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)
        return self.attribute
