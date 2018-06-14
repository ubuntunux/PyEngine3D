import numpy as np

from Utilities import *
from Common import logger
from App import CoreManager
from Object import StaticActor


class MainLight(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)
        self.light_color = Float4(*object_data.get('light_color', (1.0, 1.0, 1.0, 1.0)))
        self.shadow_view_projection = MATRIX4_IDENTITY.copy()

    def get_attribute(self):
        super().get_attribute()
        self.attributes.set_attribute('light_color', self.light_color)
        return self.attributes

    def set_attribute(self, attributeName, attributeValue, attribute_index):
        super().set_attribute(attributeName, attributeValue, attribute_index)
        if attributeName == 'light_color':
            self.light_color[:] = attributeValue[:]

    def get_save_data(self):
        save_data = StaticActor.get_save_data(self)
        save_data['light_color'] = self.light_color.tolist()
        return save_data

    def update(self, current_camera):
        self.transform.update_transform(update_view_transform=True)

        if current_camera:
            shadow_distance = 50.0 / current_camera.meter_per_unit
            width, height = shadow_distance * 0.5, shadow_distance * 0.5
            projection = ortho(-width, width, -height, height, -shadow_distance, shadow_distance)

            lightPosMatrix = get_translate_matrix(*(-current_camera.transform.get_pos()))
            self.shadow_view_projection[...] = np.dot(np.dot(lightPosMatrix, self.transform.inverse_matrix), projection)


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

    def set_attribute(self, attributeName, attributeValue, attribute_index):
        super().set_attribute(attributeName, attributeValue, attribute_index)
        if attributeName == 'light_color':
            self.light_color[:] = attributeValue[:]
        elif hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)

    def get_save_data(self):
        save_data = StaticActor.get_save_data(self)
        save_data['light_color'] = self.light_color.tolist()
        save_data['light_radius'] = self.light_radius
        return save_data

    def update(self):
        self.transform.update_transform()
