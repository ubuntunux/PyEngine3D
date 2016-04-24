import numpy as np

from Core import logger, config
from Utilities import *
from Object import TransformObject

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
class Camera(TransformObject):
    def __init__(self):
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

    def cameraInfos(self):
        text = "Position : " + " ".join(["%2.2f" % i for i in self.pos])
        text += "\nRotation : " + " ".join(["%2.2f" % i for i in self.rot])
        text += "\nFront : " + " ".join(["%2.2f" % i for i in self.front])
        text += "\nRight : " + " ".join(["%2.2f" % i for i in self.right])
        text += "\nUp : " + " ".join(["%2.2f" % i for i in self.up])
        return text