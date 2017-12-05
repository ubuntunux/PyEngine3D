import numpy as np

from Utilities import *
from Common import logger
from App import CoreManager
from Object import StaticActor


class Light(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)
        self.lightColor = Float4(*object_data.get('lightColor', (1.0, 1.0, 1.0, 1.0)))
        self.shadow_view_projection = MATRIX4_IDENTITY.copy()

    def getAttribute(self):
        super().getAttribute()
        self.attributes.setAttribute('lightColor', self.lightColor)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        super().setAttribute(attributeName, attributeValue, attribute_index)
        if attributeName == 'lightColor':
            self.lightColor[:] = attributeValue[:]

    def get_save_data(self):
        save_data = StaticActor.get_save_data(self)
        save_data['lightColor'] = self.lightColor.tolist()
        return save_data

    def update(self, current_camera):
        self.transform.updateTransform(update_view_transform=True)

        if current_camera:
            shadow_distance = 50.0 / current_camera.meter_per_unit
            width, height = shadow_distance * 0.5, shadow_distance * 0.5
            projection = ortho(-width, width, -height, height, -shadow_distance, shadow_distance)

            lightPosMatrix = getTranslateMatrix(*(-current_camera.transform.getPos()))
            # shadow_projection[3, 0:3] = light.transform.front * -shadow_distance
            self.shadow_view_projection[...] = np.dot(np.dot(lightPosMatrix, self.transform.inverse_matrix), projection)
