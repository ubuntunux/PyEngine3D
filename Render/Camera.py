from Core import coreManager, logger
from Utilities import Singleton


#------------------------------#
# CLASS : CameraManager
#------------------------------#
class CameraManager(Singleton):
    def __init__(self):
        self.cameras = []
        self.mainCamera = None
        # regist
        coreManager.regist("Camera Manager", self)

    def initialize(self):
        self.cameras = []
        self.mainCamera = Camera(45.0, 0.1, 100.0)
        logger.info("Initialize Camera Manager.")

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

#------------------------------#
# Globals
#------------------------------#
cameraManager = CameraManager()