from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.Render import Plane
from PyEngine3D.OpenGLContext import InstanceBuffer
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

        self.height_map_size = np.array(object_data.get('height_map_size', [10.0, 10.0]), dtype=np.float32)

        self.width = object_data.get('width', 10)
        self.height = object_data.get('height', 10)

        self.instance_offset = None
        self.set_instance_offset(self.width, self.height)
        self.instance_buffer = InstanceBuffer(name="terrain_instance_buffer", location_offset=5, element_datas=[FLOAT4_ZERO, ])

        self.subdivide_level = object_data.get('subdivide_level', 100)
        self.terrain_grid = None
        self.generate_terrain(self.subdivide_level)

        self.texture_height_map = self.resource_manager.get_texture(object_data.get('texture_height_map', "common.noise"))
        self.terrain_render = self.resource_manager.get_material_instance('terrain.render')

        self.attributes = Attributes()

    def get_save_data(self):
        save_data = dict(
            is_render_terrain=self.is_render_terrain,
            pos=self.transform.pos,
            rot=self.transform.rot,
            scale=self.transform.scale,
            height_map_size=self.height_map_size,
            width=self.width,
            height=self.height,
            subdivide_level=self.subdivide_level,
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
            self.transform.update_transform()
        elif attribute_name == 'rot':
            self.transform.set_rotation(attribute_value)
            self.transform.update_transform()
        elif attribute_name == 'scale':
            self.transform.set_scale(attribute_value)
            self.transform.update_transform()
        elif attribute_name == 'texture_height_map':
            self.texture_height_map = self.resource_manager.get_texture(attribute_value)
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)
            if attribute_name in ('width', 'height'):
                self.set_instance_offset(self.width, self.height)
            elif attribute_name in 'subdivide_level':
                self.generate_terrain(self.subdivide_level)
        return self.attributes

    def generate_terrain(self, subdivide_level):
        self.terrain_grid = Plane("Terrain_Grid", mode=GL_QUADS, width=subdivide_level, height=subdivide_level, xz_plane=True)

    def set_instance_offset(self, width, height):
        count = width * height
        self.instance_offset = np.zeros(count, (np.float32, 4))
        i = 0
        for y in range(height):
            for x in range(width):
                self.instance_offset[i][0] = x
                self.instance_offset[i][1] = y
                i += 1

    def update(self, delta):
        pass

    def render_terrain(self):
        material_instance = self.terrain_render
        material_instance.use_program()
        material_instance.bind_material_instance()
        material_instance.bind_uniform_data('height_map_size', self.height_map_size)
        material_instance.bind_uniform_data('model', self.transform.matrix)
        material_instance.bind_uniform_data('texture_height_map', self.texture_height_map)
        self.terrain_grid.get_geometry().draw_elements_instanced(len(self.instance_offset), self.instance_buffer, [self.instance_offset, ])

