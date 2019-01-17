from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.Render import Plane
from PyEngine3D.Utilities import *


class Terrain:
    def __init__(self, **object_data):
        self.renderer = CoreManager.instance().renderer
        self.scene_manager = CoreManager.instance().scene_manager
        self.resource_manager = CoreManager.instance().resource_manager

        self.name = object_data.get('name', 'terrain')
        self.is_render_terrain = object_data.get('is_render_terrain', True)

        self.transform = TransformObject()
        self.transform.set_pos(object_data.get('pos', [0, 0, 0]))
        self.transform.set_rotation(object_data.get('rot', [0, 0, 0]))
        self.transform.set_scale(object_data.get('scale', [1, 1, 1]))

        self.width = object_data.get('width', 10)
        self.height = object_data.get('height', 10)
        self.tessellation_level = object_data.get('tessellation_level', 1.0)

        self.terrain_grid = None
        self.generate_terrain()

        self.texture_height_map = self.resource_manager.get_texture(object_data.get('texture_height_map', "common.noise"))
        self.terrain_render = self.resource_manager.get_material_instance('terrain.render')

        self.attributes = Attributes()

    def get_save_data(self):
        save_data = dict(
            is_render_terrain=self.is_render_terrain,
            pos=self.transform.pos,
            rot=self.transform.rot,
            scale=self.transform.scale,
            width=self.width,
            height=self.height,
            tessellation_level=self.tessellation_level,
            texture_height_map=self.texture_height_map.name,
        )
        return save_data

    def get_attribute(self):
        save_data = self.get_save_data()
        for key in save_data:
            self.attributes.set_attribute(key, save_data[key])
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        if attribute_name == 'pos':
            self.transform.set_pos(attribute_value)
        elif attribute_name == 'rot':
            self.transform.set_rotation(attribute_value)
        elif attribute_name == 'scale':
            self.transform.set_scale(attribute_value)
        elif attribute_name == 'texture_height_map':
            self.texture_height_map = self.resource_manager.get_texture(attribute_value)
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)
            if attribute_name in ('width', 'height'):
                self.generate_terrain()
        return self.attributes

    def generate_terrain(self):
        self.terrain_grid = Plane("Terrain_Grid", mode=GL_QUADS, width=self.width, height=self.height, xz_plane=True)

    def update(self, delta):
        self.transform.update_transform()

    def render_terrain(self):
        material_instance = self.terrain_render
        material_instance.use_program()
        material_instance.bind_material_instance()
        material_instance.bind_uniform_data('tessellation_level', self.tessellation_level)
        material_instance.bind_uniform_data('model', self.transform.matrix)
        material_instance.bind_uniform_data('texture_height_map', self.texture_height_map)
        self.terrain_grid.get_geometry().draw_elements()

