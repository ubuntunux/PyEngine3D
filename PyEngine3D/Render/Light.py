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

        self.shadow_samples = object_data.get('shadow_samples', SHADOW_SAMPLES)
        self.shadow_exp = object_data.get('shadow_exp', SHADOW_EXP)
        self.shadow_bias = object_data.get('shadow_bias', SHADOW_BIAS)
        self.shadow_width = object_data.get('shadow_width', SHADOW_DISTANCE)
        self.shadow_height = object_data.get('shadow_height', SHADOW_DISTANCE)
        self.shadow_depth = object_data.get('shadow_depth', SHADOW_DISTANCE)
        self.shadow_orthogonal = Matrix4()
        self.shadow_view_projection = Matrix4()
        self.changed = False

        self.update_shadow_orthogonal()

    def reset_changed(self):
        self.changed = False

    def update_shadow_orthogonal(self):
        ortho(self.shadow_orthogonal,
              -self.shadow_width, self.shadow_width,
              -self.shadow_height, self.shadow_height,
              -self.shadow_depth, self.shadow_depth)
        self.changed = True

    def get_attribute(self):
        super().get_attribute()
        self.attributes.set_attribute('light_color', self.light_color)
        self.attributes.set_attribute('shadow_width', self.shadow_width)
        self.attributes.set_attribute('shadow_height', self.shadow_height)
        self.attributes.set_attribute('shadow_depth', self.shadow_depth)
        self.attributes.set_attribute('shadow_exp', self.shadow_exp)
        self.attributes.set_attribute('shadow_bias', self.shadow_bias)
        self.attributes.set_attribute('shadow_samples', self.shadow_samples)
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        if 'light_color' == attribute_name:
            self.light_color[...] = attribute_value
            self.changed = True
        elif attribute_name in ('shadow_width', 'shadow_height', 'shadow_depth'):
            setattr(self, attribute_name, attribute_value)
            self.update_shadow_orthogonal()
        else:
            super().set_attribute(attribute_name, attribute_value, item_info_history, attribute_index)

    def get_save_data(self):
        save_data = StaticActor.get_save_data(self)
        save_data['light_color'] = self.light_color.tolist()
        save_data['shadow_width'] = self.shadow_width
        save_data['shadow_height'] = self.shadow_height
        save_data['shadow_depth'] = self.shadow_depth
        save_data['shadow_exp'] = self.shadow_exp
        save_data['shadow_bias'] = self.shadow_bias
        save_data['shadow_samples'] = self.shadow_samples
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
