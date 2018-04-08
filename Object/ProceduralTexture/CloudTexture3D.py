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
        self.scale = data.get('scale', 1.0)
        self.density = data.get('density', 1.0)
        self.noise_persistance = data.get('noise_persistance', 0.7)
        self.noise_scale = data.get('noise_scale', 6)
        self.noise_contrast = data.get('noise_contrast', 1.0)
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

        mat = resource_manager.getMaterialInstance('examples.cloud_noise_3d')
        mat.use_program()
        mat.bind_uniform_data('density', self.density)
        mat.bind_uniform_data('noise_persistance', self.noise_persistance)
        mat.bind_uniform_data('noise_scale', self.noise_scale)
        mat.bind_uniform_data('noise_contrast', self.noise_contrast)
        mat.bind_uniform_data('noise_seed', core_manager.currentTime)

        # render spheres
        count = 500
        spheres = np.zeros(shape=(count, 4), dtype=np.float32)
        for i in range(count):
            x = random.random()
            y = random.random()
            z = random.random()
            r = random.uniform(0.5 * self.scale, self.scale)
            spheres[i][...] = [x, y, z, r]
        mat.bind_uniform_data('spheres', spheres, num=count)

        for i in range(texture.depth):
            mat.bind_uniform_data('depth', i / texture.depth)
            renderer.framebuffer_manager.bind_framebuffer(texture, target_layer=i)
            renderer.postprocess.draw_elements()

        # # render small spheres
        # renderer.restore_blend_state_prev()
        # renderer.set_blend_state(True, equation=GL_MAX, func_src=GL_ONE, func_dst=GL_ONE)
        #
        # spheres = np.zeros(shape=(count, 4), dtype=np.float32)
        # for i in range(count):
        #     x = random.random()
        #     y = random.random()
        #     z = random.random()
        #     r = random.uniform(0.5 * self.scale * 0.5, self.scale * 0.5)
        #     spheres[i][...] = [x, y, z, r]
        # mat.bind_uniform_data('spheres', spheres, num=count)
        #
        # for i in range(texture.depth):
        #     mat.bind_uniform_data('depth', i / texture.depth)
        #     renderer.framebuffer_manager.bind_framebuffer(texture, target_layer=i)
        #     renderer.postprocess.draw_elements()

        renderer.restore_blend_state_prev()

    def get_save_data(self):
        save_data = dict(
            texture_type=self.__class__.__name__,
            texture_name=self.texture_name,
            width=self.width,
            height=self.height,
            depth=self.depth,
            scale=self.scale,
            density=self.density,
            noise_persistance=self.noise_persistance,
            noise_scale=self.noise_scale,
            noise_contrast=self.noise_contrast,
        )
        return save_data

    def getAttribute(self):
        self.attribute.setAttribute("texture_name", self.texture_name)
        self.attribute.setAttribute("width", self.width)
        self.attribute.setAttribute("height", self.height)
        self.attribute.setAttribute("depth", self.depth)
        self.attribute.setAttribute("scale", self.scale)
        self.attribute.setAttribute("density", self.density)
        self.attribute.setAttribute("noise_persistance", self.noise_persistance)
        self.attribute.setAttribute("noise_scale", self.noise_scale)
        self.attribute.setAttribute("noise_contrast", self.noise_contrast)
        return self.attribute

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)
        return self.attribute
