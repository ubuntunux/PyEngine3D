import numpy as np

from __main__ import logger, config
from Utilities import Singleton


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
        self.pos = np.array([0.0, 0.0, -6.0])

#------------------------------#
# Globals
#------------------------------#
cameraManager = CameraManager()