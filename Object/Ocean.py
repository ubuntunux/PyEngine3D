import numpy as np

from OpenGL.GL import *

from Common import logger
from App import CoreManager
from Object import Plane
from OpenGLContext import CreateTexture, Texture2D, Texture2DArray, Texture3D, VertexArrayBuffer, FrameBuffer
from Utilities import *


class Ocean:
    def __init__(self, **object_data):
        self.name = object_data.get('name', 'ocean')
        self.height = object_data.get('height', 0.0)
        self.is_render_ocean = True
        self.attributes = Attributes()

        resource_manager = CoreManager.instance().resource_manager
        self.material_instance = resource_manager.getMaterialInstance('ocean')

        self.mesh = Plane(width=200, height=200)
        self.geometry = self.mesh.get_geometry()
        self.geometry.vertex_buffer.create_instance_buffer(instance_name="offset",
                                                           layout_location=5,
                                                           element_data=FLOAT2_ZERO)
        # instanced grid
        # self.grid_size = Float2(100.0, 100.0)
        # self.grid_count = 1
        # self.offsets = np.array(
        #     [Float2(i % self.grid_count, i // self.grid_count) for i in range(self.grid_count * self.grid_count)],
        #     dtype=np.float32)

    def getAttribute(self):
        self.attributes.setAttribute('height', self.height)
        self.attributes.setAttribute('is_render_ocean', self.is_render_ocean)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)

    def get_save_data(self):
        save_data = dict()
        save_data['height'] = self.height
        return save_data

    def update(self, delta):
        pass

    def render_ocean(self, atmoshpere, texture_depth, texture_probe, texture_shadow, texture_scene_reflect):
        self.material_instance.use_program()
        self.material_instance.bind_material_instance()
        self.material_instance.bind_uniform_data('height', self.height)

        self.material_instance.bind_uniform_data('texture_depth', texture_depth)
        self.material_instance.bind_uniform_data('texture_probe', texture_probe)
        self.material_instance.bind_uniform_data('texture_shadow', texture_shadow)
        self.material_instance.bind_uniform_data('texture_scene_reflect', texture_scene_reflect)

        # Bind Atmosphere
        atmoshpere.bind_precomputed_atmosphere(self.material_instance)

        self.geometry.bind_vertex_buffer()
        self.geometry.draw_elements()

        # instanced grid
        # self.material_instance.bind_uniform_data('grid_size', self.grid_size)
        # self.geometry.bind_instance_buffer(instance_name="offset",
        #                                    instance_data=self.offsets,
        #                                    divisor=1)
        # self.geometry.bind_vertex_buffer()
        # self.geometry.draw_elements_instanced(len(self.offsets))
