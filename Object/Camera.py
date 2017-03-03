import numpy as np

from Core import logger, config
from Utilities import *
from Object import BaseObject


# ------------------------------ #
# CLASS : Camera
# ------------------------------ #
class Camera(BaseObject):
    def __init__(self, name):
        BaseObject.__init__(self, name, (0, 0, 0), None, None)

        # get properties
        self.fov = config.Camera.fov
        self.near = config.Camera.near
        self.far = config.Camera.far
        self.move_speed = config.Camera.move_speed
        self.pan_speed = config.Camera.pan_speed
        self.rotation_speed = config.Camera.rotation_speed

        # log
        logger.info("Create Camera : %s" % self.name)

    # override : draw
    def draw(self, *args, **kargs):
        pass

    def update(self):
        self.transform.updateTransform()
        self.transform.updateInverseTransform() # update view matrix
