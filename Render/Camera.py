from Configure import config
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
        coreManager.regist(self.__class__.__name__, self)
        logger.info("regist " + self.__class__.__name__)

    def initialize(self):
        self.cameras = []
        camera = config.Camera
        logger.info("initialize " + self.__class__.__name__)

        self.mainCamera = Camera(camera.fov, camera.near, camera.far)
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

#------------------------------#
# Globals
#------------------------------#
cameraManager = CameraManager()