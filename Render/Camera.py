import numpy as np

from Core import logger, config
from Utilities import Singleton

WORLD_UP = np.array([0.0, 1.0, 0.0])

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
        camera = Camera(config.Camera.fov, config.Camera.near, config.Camera.far)
        self.cameras.append(camera)
        self.mainCamera = camera
        logger.info("MainCamera Fov(%.1f), Near(%.1f), Far(%.1f)" % (camera.fov, camera.near, camera.far))

    def getMainCamera(self):
        return self.mainCamera


#------------------------------#
# CLASS : Camera
#------------------------------#
class Camera:
    def __init__(self, fov, near, far):
        self.fov = fov
        self.near = near
        self.far = far
        # x, y, z
        self.pos = np.array([0.0, 0.0, -6.0])
        # pitch, yaw, roll
        self.rot = np.array([0.0, 0.0, 0.0])
        # front - Z Axis
        self.front = np.array([0.0, 0.0, 1.0])
        # up - Y Axis
        self.front = np.array([0.0, 1.0, 0.0])
        # right - X Axis
        self.right = np.array([1.0, 0.0, 0.0])

    def calculateVectors(self):
        self.front.flat = [-np.sin(np.deg2rad(self.rot[1])), np.sin(np.deg2rad(self.rot[0])), np.cos(np.deg2rad(self.rot[1]))]
        self.front /= np.linalg.norm(self.front)

        self.right = np.cross(WORLD_UP, self.front)
        self.up = np.cross(self.right, self.front)