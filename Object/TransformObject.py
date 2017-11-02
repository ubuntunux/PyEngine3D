import numpy as np

import time
from Utilities import *


class TransformObject:
    def __init__(self, local=None):
        self.quat = Float4(0.0, 0.0, 0.0, 1.0)
        self.local = local if local is not None else Matrix4()

        self.moved = True
        self.rotated = True
        self.scaled = True
        self.updated = True
        self.force_update = True

        self.left = WORLD_LEFT.copy()
        self.up = WORLD_UP.copy()
        self.front = WORLD_FRONT.copy()

        self.pos = Float3()
        self.rot = Float3()
        self.scale = Float3(1, 1, 1)

        self.prev_Pos = Float3()
        self.prev_Rot = Float3()
        self.prev_Scale = Float3(1, 1, 1)

        self.translateMatrix = Matrix4()
        self.rotationMatrix = Matrix4()
        self.scaleMatrix = Matrix4()

        self.matrix = Matrix4()
        self.inverse_matrix = Matrix4()

        self.prev_matrix = Matrix4()
        self.prev_inverse_matrix = Matrix4()

        self.updateTransform()

    def resetTransform(self):
        self.moved = True
        self.rotated = True
        self.scaled = True
        self.updated = True
        self.force_update = True
        self.setPos(Float3())
        self.setRot(Float3())
        self.setScale(Float3(1, 1, 1))
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

    def move(self, vDelta):
        self.moved = True
        self.pos[...] = self.pos + vDelta

    def moveToFront(self, delta):
        self.moved = True
        self.pos[...] = self.pos + self.front * delta

    def moveToLeft(self, delta):
        self.moved = True
        self.pos[...] = self.pos + self.left * delta

    def moveToUp(self, delta):
        self.moved = True
        self.pos[...] = self.pos + self.up * delta

    def moveX(self, delta):
        self.moved = True
        self.pos[0] += delta

    def moveY(self, delta):
        self.moved = True
        self.pos[1] += delta

    def moveZ(self, delta):
        self.moved = True
        self.pos[2] += delta

    # Rotation
    def getRotation(self):
        return self.rot

    def setRot(self, rot):
        self.rotated = True
        self.rot[...] = rot

    def setPitch(self, pitch):
        self.rotated = True
        if pitch > TWO_PI or pitch < 0.0:
            pitch %= TWO_PI
        self.rot[0] = pitch

    def setYaw(self, yaw):
        self.rotated = True
        if yaw > TWO_PI or yaw < 0.0:
            yaw %= TWO_PI
        self.rot[1] = yaw

    def setRoll(self, roll):
        self.rotated = True
        if roll > TWO_PI or roll < 0.0:
            roll %= TWO_PI
        self.rot[2] = roll

    def rotationPitch(self, delta=0.0):
        self.rotated = True
        self.rot[0] += delta
        if self.rot[0] > TWO_PI or self.rot[0] < 0.0:
            self.rot[0] %= TWO_PI

    def rotationYaw(self, delta=0.0):
        self.rotated = True
        self.rot[1] += delta
        if self.rot[1] > TWO_PI or self.rot[1] < 0.0:
            self.rot[1] %= TWO_PI

    def rotationRoll(self, delta=0.0):
        self.rotated = True
        self.rot[2] += delta
        if self.rot[2] > TWO_PI or self.rot[2] < 0.0:
            self.rot[2] %= TWO_PI

    # Scale
    def getScale(self):
        return self.scale

    def setScale(self, vScale):
        self.scaled = True
        self.scale[...] = vScale

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
        was_updated = self.updated
        self.updated = False

        if self.moved and any(self.prev_Pos != self.pos) or self.force_update:
            self.prev_Pos[...] = self.pos
            setTranslateMatrix(self.translateMatrix, self.pos[0], self.pos[1], self.pos[2])
            self.moved = False
            self.updated = True

        if self.rotated and any(self.prev_Rot != self.rot) or self.force_update:
            self.prev_Rot[...] = self.rot
            self.rotated = False
            self.updated = True

            # Matrix Rotation - faster
            matrix_rotation(*self.rot, self.rotationMatrix)
            matrix_to_vectors(self.rotationMatrix, self.left, self.up, self.front)

            # Euler Rotation - slow
            # p = getRotationMatrixX(self.rot[0])
            # y = getRotationMatrixY(self.rot[1])
            # r = getRotationMatrixZ(self.rot[2])
            # self.rotationMatrix = np.dot(p, np.dot(y, r))
            # matrix_to_vectors(self.rotationMatrix, self.right, self.up, self.front)

            # Quaternion Rotation - slower
            # euler_to_quaternion(*self.rot, self.quat)
            # quaternion_to_matrix(self.quat, self.rotationMatrix)
            # matrix_to_vectors(self.rotationMatrix, self.right, self.up, self.front)

        if self.scaled and any(self.prev_Scale != self.scale) or self.force_update:
            self.prev_Scale[...] = self.scale
            setScaleMatrix(self.scaleMatrix, self.scale[0], self.scale[1], self.scale[2])
            self.scaled = False
            self.updated = True

        if self.updated or self.force_update:
            self.force_update = False
            self.prev_matrix[...] = self.matrix
            self.matrix[...] = dot_arrays(self.local, self.scaleMatrix, self.rotationMatrix, self.translateMatrix)
        return was_updated

    def updateInverseTransform(self):
        if self.updated:
            self.prev_inverse_matrix[...] = self.inverse_matrix
            self.inverse_matrix[...] = np.linalg.inv(self.matrix)

    def getTransformInfos(self):
        text = "\tPosition : " + " ".join(["%2.2f" % i for i in self.pos])
        text += "\n\tRotation : " + " ".join(["%2.2f" % i for i in self.rot])
        text += "\n\tFront : " + " ".join(["%2.2f" % i for i in self.front])
        text += "\n\tLeft : " + " ".join(["%2.2f" % i for i in self.left])
        text += "\n\tUp : " + " ".join(["%2.2f" % i for i in self.up])
        text += "\n\tMatrix"
        text += "\n\t" + " ".join(["%2.2f" % i for i in self.matrix[0, :]])
        text += "\n\t" + " ".join(["%2.2f" % i for i in self.matrix[1, :]])
        text += "\n\t" + " ".join(["%2.2f" % i for i in self.matrix[2, :]])
        text += "\n\t" + " ".join(["%2.2f" % i for i in self.matrix[3, :]])
        return text
