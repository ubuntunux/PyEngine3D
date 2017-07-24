import numpy as np

from Common import logger
from App.CoreManager import CoreManager
from Object import StaticActor
from Utilities import *


# ------------------------------ #
# CLASS : Camera
# ------------------------------ #
class Camera(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)

        self.aspect = 0.0
        self.fov = 0.0
        self.near = 0.0
        self.far = 0.0
        self.projection = Matrix4()
        self.view_projection = Matrix4()
        self.move_speed = 0.0
        self.pan_speed = 0.0
        self.rotation_speed = 0.0

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

    def get_view_dir(self):
        return -self.transform.front

    def get_view_matrix(self):
        return self.transform.inverse_matrix

    def update_projection(self, aspect):
        self.projection = perspective(self.fov, aspect, self.near, self.far)
        # self.projection = ortho(width * -0.5, width * 0.5, height * -0.5, height * 0.5, self.near, self.far)

    def update(self):
        self.transform.updateTransform()
        self.transform.updateInverseTransform()  # update view matrix
        self.view_projection[...] = np.dot(self.transform.inverse_matrix, self.projection)[...]
