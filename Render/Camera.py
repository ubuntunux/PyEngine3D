import numpy as np

from Core import logger, config
from Utilities import *

#------------------------------#
# CLASS : CameraManager
#------------------------------#
class CameraManager(Singleton):
    def __init__(self):
        self.cameras = []
        self.mainCamera = None
        self.coreManager = None

    def initialize(self, coreManager):
        logger.info("initialize " + self.__class__.__name__)
        self.coreManager = coreManager
        self.cameras = []

        # add main camera
        camera = Camera()
        self.cameras.append(camera)
        self.mainCamera = camera
        logger.info("MainCamera Fov(%.1f), Near(%.1f), Far(%.1f)" % (camera.fov, camera.near, camera.far))

    def getMainCamera(self):
        return self.mainCamera


#------------------------------#
# CLASS : Camera
#------------------------------#
class Camera:
    def __init__(self):
        # get properties
        self.fov = config.Camera.fov
        self.near = config.Camera.near
        self.far = config.Camera.far
        self.pan_speed = config.Camera.pan_speed
        self.rotation_speed = config.Camera.rotation_speed
        self.matrix = np.eye(4,dtype=np.float32)

        self.pos = np.array([0.0, 0.0, 0.0]) # x, y, z
        self.rot = np.array([0.0, 0.0, 0.0]) # pitch, yaw, roll
        self.front = np.array([0.0, 0.0, 1.0]) # front - Z Axis
        self.up = np.array([0.0, 1.0, 0.0]) # up - Y Axis
        self.right = np.array([1.0, 0.0, 0.0]) # right - X Axis

    def initialize(self):
        self.matrix = np.eye(4,dtype=np.float32)