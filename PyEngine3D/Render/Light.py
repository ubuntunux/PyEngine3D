import numpy as np

from PyEngine3D.Utilities import *
from PyEngine3D.Common import logger
from PyEngine3D.Common.Constants import *
from PyEngine3D.App import CoreManager
from .Actor import StaticActor


class MainLight(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)
        self.light_color = Float4(*object_data.get('light_color', (1.0, 1.0, 1.0, 1.0)))

        self.transform.set_rotation(object_data.get('rot', [-1.0, 0, 0]))

        self.last_shadow_camera = None
        self.last_shadow_position = FLOAT3_ZERO.copy()

        self.shadow_width = SHADOW_DISTANCE * 1.0
        self.shadow_height = SHADOW_DISTANCE * 1.0
        self.shadow_depth = SHADOW_DISTANCE * 1.0
        self.shadow_orthogonal = ortho(-self.shadow_width, self.shadow_width,
                                       -self.shadow_height, self.shadow_height,
                                       -self.shadow_depth, self.shadow_depth)
        self.shadow_view_projection = MATRIX4_IDENTITY.copy()
        self.changed = False

    def reset_changed(self):
        self.changed = False

    def get_attribute(self):
        super().get_attribute()
        self.attributes.set_attribute('light_color', self.light_color)
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        super().set_attribute(attribute_name, attribute_value, item_info_history, attribute_index)
        if attribute_name == 'light_color':
            self.light_color[:] = attribute_value[:]
            self.changed = True

    def get_save_data(self):
        save_data = StaticActor.get_save_data(self)
        save_data['light_color'] = self.light_color.tolist()
        return save_data

    def update(self, current_camera):
        changed = self.transform.update_transform(update_inverse_matrix=True)
        self.changed = self.changed or changed

        if current_camera is not None:
            camera_pos = current_camera.transform.get_pos()

            self.last_shadow_camera = current_camera
            self.last_shadow_position[...] = camera_pos
            set_translate_matrix(self.shadow_view_projection, *(-camera_pos))
            self.shadow_view_projection[...] = np.dot(np.dot(self.shadow_view_projection, self.transform.inverse_matrix), self.shadow_orthogonal)


class PointLight(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)
        self.light_color = Float3(*object_data.get('light_color', (1.0, 1.0, 1.0)))
        self.light_radius = object_data.get('light_radius', 10.0)

    def get_attribute(self):
        super().get_attribute()
        self.attributes.set_attribute('light_color', self.light_color)
        self.attributes.set_attribute('light_radius', self.light_radius)
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        super().set_attribute(attribute_name, attribute_value, item_info_history, attribute_index)
        if attribute_name == 'light_color':
            self.light_color[:] = attribute_value[:]
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)

    def get_save_data(self):
        save_data = StaticActor.get_save_data(self)
        save_data['light_color'] = self.light_color.tolist()
        save_data['light_radius'] = self.light_radius
        return save_data

    def update(self):
        self.transform.update_transform()
