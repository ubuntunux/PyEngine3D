from Common import logger
from App.CoreManager import CoreManager
from Object import StaticMeshInst


# ------------------------------ #
# CLASS : Camera
# ------------------------------ #
class Camera(StaticMeshInst):
    def __init__(self, name, object_data):
        StaticMeshInst.__init__(self, name, object_data)

        self.fov = None
        self.near = None
        self.far = None
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
        StaticMeshInst.getAttribute(self)
        self.attributes.setAttribute('fov', self.fov)
        self.attributes.setAttribute('near', self.near)
        self.attributes.setAttribute('far', self.far)
        self.attributes.setAttribute('move_speed', self.move_speed)
        self.attributes.setAttribute('pan_speed', self.pan_speed)
        self.attributes.setAttribute('rotation_speed', self.rotation_speed)
        return self.attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        StaticMeshInst.setAttribute(self, attributeName, attributeValue, attribute_index)
        if hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)

    def update(self):
        self.transform.updateTransform()
        self.transform.updateInverseTransform()  # update view matrix
