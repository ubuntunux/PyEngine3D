import numpy as np

from Core import logger, config
from Utilities import *
from Object import TransformObject


#------------------------------#
# CLASS : Camera
#------------------------------#
class Camera(TransformObject):
    def __init__(self, name):
        self.name = name
        TransformObject.__init__(self)

        # get properties
        self.fov = config.Camera.fov
        self.near = config.Camera.near
        self.far = config.Camera.far
        self.pan_speed = config.Camera.pan_speed
        self.rotation_speed = config.Camera.rotation_speed

        # transform
        self.matrix = np.eye(4, dtype=np.float32)
        self.pos = np.zeros(3, dtype=np.float32) # X, Y, Z
        self.rot = np.zeros(3, dtype=np.float32) # pitch, yaw, roll
        self.right = np.zeros(3, dtype=np.float32) # X Axis
        self.up = np.zeros(3, dtype=np.float32) # Y Axis
        self.front = np.zeros(3, dtype=np.float32) # Z Axis

        # initTransform
        self.resetTransform()
        # log
        logger.info("Create Camera : %s", self.name)