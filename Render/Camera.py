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
        self.moved = False
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

        # update matrix
        self.updateMatrix()

    def reset(self):
        self.pos = np.zeros(3, dtype=np.float32) # X, Y, Z
        self.rot = np.zeros(3, dtype=np.float32) # pitch, yaw, roll
        self.updateMatrix()

    def move(self, deltaX=0.0, deltaY=0.0, deltaZ=0.0):
        self.pos += (self.right*deltaX + self.up*deltaY + self.front*deltaZ) * self.pan_speed

    def moveX(self, delta):
        self.pos += self.right * self.pan_speed * delta

    def moveY(self, delta):
        self.pos += self.up * self.pan_speed * delta

    def moveZ(self, delta):
        self.pos += self.front * self.pan_speed * delta

    def rotationPitch(self, delta=0.0):
        self.rot[0] += delta * self.rotation_speed
        if self.rot[0] > two_pi: self.rot[0] -= two_pi
        elif self.rot[0] < 0.0: self.rot[0] += two_pi

    def rotationYaw(self, delta=0.0):
        self.rot[1] += delta * self.rotation_speed
        if self.rot[1] > two_pi: self.rot[1] -= two_pi
        elif self.rot[1] < 0.0: self.rot[1] += two_pi

    def rotationRoll(self, delta=0.0):
        self.rot[2] += delta * self.rotation_speed
        if self.rot[2] > two_pi: self.rot[2] -= two_pi
        elif self.rot[2] < 0.0: self.rot[2] += two_pi

    def updateMatrix(self):
        self.matrix = np.eye(4,dtype=np.float32)
        translate(self.matrix, *self.pos)
        rotateZ(self.matrix, self.rot[2])
        rotateY(self.matrix, self.rot[1])
        rotateX(self.matrix, self.rot[0])

        self.front = self.matrix[:3,2]
        self.right = self.matrix[:3,0]
        self.up = self.matrix[:3,1]

    def cameraInfos(self):
        text = "Position : " + " ".join(["%2.2f" % i for i in self.pos])
        text += "\nRotation : " + " ".join(["%2.2f" % i for i in self.rot])
        text += "\nFront : " + " ".join(["%2.2f" % i for i in self.front])
        text += "\nRight : " + " ".join(["%2.2f" % i for i in self.right])
        text += "\nUp : " + " ".join(["%2.2f" % i for i in self.up])
        return text