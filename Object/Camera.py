import numpy as np

from Core import logger, config
from Utilities import *
from Object import BaseObject


#------------------------------#
# CLASS : Camera
#------------------------------#
class Camera(BaseObject):
    def __init__(self, name):
        BaseObject.__init__(self, name)

        # get properties
        self.fov = config.Camera.fov
        self.near = config.Camera.near
        self.far = config.Camera.far
        self.pan_speed = config.Camera.pan_speed
        self.rotation_speed = config.Camera.rotation_speed

        # log
        logger.info("Create Camera : %s", self.name)

    def draw(self, *args, **kargs):
        pass