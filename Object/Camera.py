import numpy as np

from Common import logger
from App.CoreManager import CoreManager
from Object import StaticActor
from Utilities import perspective, ortho


# ------------------------------ #
# CLASS : Camera
# ------------------------------ #
class Camera(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)

        self.fov = None
        self.near = None
        self.far = None
        self.perspective = np.eye(4, dtype=np.float32)
        self.ortho = np.eye(4, dtype=np.float32)
        self.vp_matrix = np.eye(4, dtype=np.float32)
        self.move_speed = None
        self.pan_speed = None
        self.rotation_speed = None

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

    def update_viewport(self, width, height, viewportRatio):
        self.perspective = perspective(self.fov, viewportRatio, self.near, self.far)
        self.ortho = ortho(0, width, 0, height, self.near, self.far)

    def update(self):
        self.transform.updateTransform()
        self.transform.updateInverseTransform()  # update view matrix
        self.vp_matrix[...] = np.dot(self.transform.inverse_matrix, self.perspective)[...]
