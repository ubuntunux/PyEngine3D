import numpy as np

from Core import logger, config
from Utilities import *

#------------------------------#
# CLASS : TransformObject
#------------------------------#
class TransformObject:
    def __init__(self):
        self.move_speed = config.Object.move_speed
        self.rotation_speed = config.Object.rotation_speed

        self.moved = False
        self.rotated = False
        self.scaled = False

        # transform
        self.matrix = np.eye(4, dtype=np.float32)
        self.translateMatrix = np.eye(4, dtype=np.float32)
        self.rotationMatrix =  np.eye(4, dtype=np.float32)
        self.scaleMatrix = np.eye(4, dtype=np.float32)

        self.pos = np.zeros(3, dtype=np.float32) # X, Y, Z
        self.oldPos = np.zeros(3, dtype=np.float32)

        self.rot = np.zeros(3, dtype=np.float32) # pitch, yaw, roll
        self.oldRot = np.zeros(3, dtype=np.float32)
        self.right = np.zeros(3, dtype=np.float32) # X Axis
        self.up = np.zeros(3, dtype=np.float32) # Y Axis
        self.front = np.zeros(3, dtype=np.float32) # Z Axis

        self.scale = np.zeros(3, dtype=np.float32)
        self.oldScale = np.zeros(3, dtype=np.float32)

        # init transform
        self.resetTransform()

    def resetTransform(self):
        self.setPos(np.zeros(3, dtype=np.float32))
        self.setRot(np.zeros(3, dtype=np.float32))
        self.setScale(np.zeros(3, dtype=np.float32))
        self.updateTransform()

    # Translate
    def getPos(self):
        return self.pos

    def setPos(self, pos):
        self.moved = True
        self.pos[...] = pos

    def setPosX(self, x):
        self.moved = True
        self.pos[0] = x

    def setPosY(self, y):
        self.moved = True
        self.pos[1] = y

    def setPosZ(self, z):
        self.moved = True
        self.pos[2] = z

    def move(self, deltaX=0.0, deltaY=0.0, deltaZ=0.0):
        self.moved = True
        self.pos += (self.right*deltaX + self.up*deltaY + self.front*deltaZ) * self.move_speed

    def moveX(self, delta):
        self.moved = True
        self.pos += self.right * self.move_speed * delta

    def moveY(self, delta):
        self.moved = True
        self.pos += self.up * self.move_speed * delta

    def moveZ(self, delta):
        self.moved = True
        self.pos += self.front * self.move_speed * delta

    # Rotation
    def getRotation(self):
        return self.rot

    def setRot(self, rot):
        self.rotated = True
        self.rot[...] = rot

    def setPitch(self, pitch):
        self.rotated = True
        self.rot[0] = pitch
        if self.rot[0] > two_pi: self.rot[0] -= two_pi
        elif self.rot[0] < 0.0: self.rot[0] += two_pi

    def setYaw(self, yaw):
        self.rotated = True
        self.rot[1] = yaw
        if self.rot[1] > two_pi: self.rot[1] -= two_pi
        elif self.rot[1] < 0.0: self.rot[1] += two_pi

    def setRoll(self, roll):
        self.rotated = True
        self.rot[2] = roll
        if self.rot[2] > two_pi: self.rot[2] -= two_pi
        elif self.rot[2] < 0.0: self.rot[2] += two_pi

    def rotationPitch(self, delta=0.0):
        self.rotated = True
        self.rot[0] += delta * self.rotation_speed
        if self.rot[0] > two_pi: self.rot[0] -= two_pi
        elif self.rot[0] < 0.0: self.rot[0] += two_pi

    def rotationYaw(self, delta=0.0):
        self.rotated = True
        self.rot[1] += delta * self.rotation_speed
        if self.rot[1] > two_pi: self.rot[1] -= two_pi
        elif self.rot[1] < 0.0: self.rot[1] += two_pi

    def rotationRoll(self, delta=0.0):
        self.rotated = True
        self.rot[2] += delta * self.rotation_speed
        if self.rot[2] > two_pi: self.rot[2] -= two_pi
        elif self.rot[2] < 0.0: self.rot[2] += two_pi

    # Scale
    def getScale(self):
        return self.scale

    def setScale(self, scale):
        self.scaled = True
        self.scale[...] = scale

    def setScaleX(self, x):
        self.scaled = True
        self.scale[0] = x

    def setScaleY(self, y):
        self.scaled = True
        self.scale[1] = y

    def setScaleZ(self, z):
        self.scaled = True
        self.scale[2] = z

    # update Transform
    def updateTransform(self):
        update = False

        if self.moved and not all(self.oldPos == self.pos):
            update = True
            self.translateMatrix = getTranslateMatrix(*self.pos)
            self.oldPos[...] = self.pos
            self.moved = False

        if self.rotated and not all(self.oldRot == self.rot):
            update = True
            self.rotationMatrix = getRotationMatrixZ(self.rot[2])
            rotateY(self.rotationMatrix, self.rot[1])
            rotateX(self.rotationMatrix, self.rot[0])
            self.oldRot[...] = self.rot
            self.front = self.matrix[:3,2]
            self.right = self.matrix[:3,0]
            self.up = self.matrix[:3,1]
            self.rotated = False

        if self.scaled and not all(self.oldScale == self.scale):
            update = True
            self.scaleMatrix = getScaleMatrix(*self.scale)
            self.oldScale[...] = self.scale
            self.scaled = False

        if update:
            self.matrix = np.dot(self.translateMatrix, self.rotationMatrix)
            #self.matrix = np.dot(self.matrix, self.scaleMatrix)


    def getTransformInfos(self):
        text = "Position : " + " ".join(["%2.2f" % i for i in self.pos])
        text += "\nRotation : " + " ".join(["%2.2f" % i for i in self.rot])
        text += "\nFront : " + " ".join(["%2.2f" % i for i in self.front])
        text += "\nRight : " + " ".join(["%2.2f" % i for i in self.right])
        text += "\nUp : " + " ".join(["%2.2f" % i for i in self.up])
        return text