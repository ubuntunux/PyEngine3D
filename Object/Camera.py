import numpy as np

from Common import logger
from App.CoreManager import CoreManager
from Object import StaticActor
from Utilities import *


# ------------------------------ #
# CLASS : Camera
# ------------------------------ #
class Camera(StaticActor):
    def __init__(self, name, scene_manager, **object_data):
        StaticActor.__init__(self, name, **object_data)

        self.meter_per_unit = 1.0
        self.aspect = 0.0
        self.fov = 0.0
        self.near = 0.0
        self.far = 0.0
        self.scene_manager = scene_manager
        self.move_speed = 0.0
        self.pan_speed = 0.0
        self.rotation_speed = 0.0

        self.front = Float4()

        self.projection = Matrix4()

        self.view = Matrix4()
        self.view_origin = Matrix4()
        self.view_projection = Matrix4()
        self.view_origin_projection = Matrix4()

        self.prev_view = Matrix4()
        self.prev_view_origin = Matrix4()
        self.prev_view_projection = Matrix4()
        self.prev_view_origin_projection = Matrix4()

    def initialize(self):
        config = CoreManager.instance().projectManager.config
        # get properties
        self.fov = config.Camera.fov
        self.near = config.Camera.near
        self.far = config.Camera.far
        self.move_speed = config.Camera.move_speed
        self.pan_speed = config.Camera.pan_speed
        self.rotation_speed = config.Camera.rotation_speed

    def write_to_config(self, config):
        config.setValue("Camera", "meter_per_unit", self.meter_per_unit)
        config.setValue("Camera", "aspect", self.aspect)
        config.setValue("Camera", "fov", self.fov)
        config.setValue("Camera", "near", self.near)
        config.setValue("Camera", "far", self.far)
        config.setValue("Camera", "move_speed", self.move_speed)
        config.setValue("Camera", "pan_speed", self.pan_speed)
        config.setValue("Camera", "rotation_speed", self.rotation_speed)

    def getAttribute(self):
        StaticActor.getAttribute(self)
        self.attributes.setAttribute('fov', self.fov)
        self.attributes.setAttribute('near', self.near)
        self.attributes.setAttribute('far', self.far)
        self.attributes.setAttribute('move_speed', self.move_speed)
        self.attributes.setAttribute('pan_speed', self.pan_speed)
        self.attributes.setAttribute('rotation_speed', self.rotation_speed)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        StaticActor.setAttribute(self, attributeName, attributeValue, attribute_index)
        if hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)
            # update viewport
            self.scene_manager.renderer.resizeScene()

    def update_projection(self, aspect):
        self.aspect = aspect
        projection = perspective(self.fov, aspect, self.near, self.far)
        self.projection[...] = projection
        self.update(True)

    def update(self, force_update=False):
        updated = self.transform.updateTransform()
        if updated or force_update:
            self.transform.updateInverseTransform()  # update view matrix
            # negative front
            self.front = -self.transform.front

            self.prev_view = self.transform.prev_inverse_matrix
            self.prev_view_origin[...] = self.view_origin
            self.prev_view_projection[...] = self.view_projection
            self.prev_view_origin_projection[...] = self.view_origin_projection

            self.view = self.transform.inverse_matrix
            self.view_origin[...] = self.view
            self.view_origin[3, 0:3] = [0.0, 0.0, 0.0]
            self.view_projection[...] = np.dot(self.view, self.projection)
            self.view_origin_projection[...] = np.dot(self.view_origin, self.projection)

