import numpy as np

from ..Utilities import *


class TransformObject:
    def __init__(self, local=None):
        self.quat = Float4(0.0, 0.0, 0.0, 1.0)
        self.local = local if local is not None else Matrix4()

        self.moved = True
        self.rotated = True
        self.scaled = True
        self.updated = True

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

        self.update_transform(True)

    def reset_transform(self):
        self.moved = True
        self.rotated = True
        self.scaled = True
        self.updated = True
        self.set_pos(Float3())
        self.set_rotation(Float3())
        self.set_scale(Float3(1, 1, 1))
        self.update_transform(True)

    # Translate
    def get_pos(self):
        return self.pos

    def set_pos(self, pos):
        self.moved = True
        self.pos[...] = pos

    def set_pos_x(self, x):
        self.moved = True
        self.pos[0] = x

    def set_pos_y(self, y):
        self.moved = True
        self.pos[1] = y

    def set_pos_z(self, z):
        self.moved = True
        self.pos[2] = z

    def move(self, vDelta):
        self.moved = True
        self.pos[...] = self.pos + vDelta

    def move_to_front(self, delta):
        self.moved = True
        self.pos[...] = self.pos + self.front * delta

    def move_to_left(self, delta):
        self.moved = True
        self.pos[...] = self.pos + self.left * delta

    def move_to_up(self, delta):
        self.moved = True
        self.pos[...] = self.pos + self.up * delta

    def move_x(self, delta):
        self.moved = True
        self.pos[0] += delta

    def move_y(self, delta):
        self.moved = True
        self.pos[1] += delta

    def move_z(self, delta):
        self.moved = True
        self.pos[2] += delta

    # Rotation
    def get_rotation(self):
        return self.rot

    def set_rotation(self, rot):
        self.rotated = True
        self.rot[...] = rot

    def set_pitch(self, pitch):
        self.rotated = True
        if pitch > TWO_PI or pitch < 0.0:
            pitch %= TWO_PI
        self.rot[0] = pitch

    def set_yaw(self, yaw):
        self.rotated = True
        if yaw > TWO_PI or yaw < 0.0:
            yaw %= TWO_PI
        self.rot[1] = yaw

    def set_roll(self, roll):
        self.rotated = True
        if roll > TWO_PI or roll < 0.0:
            roll %= TWO_PI
        self.rot[2] = roll

    def rotation(self, rot):
        self.rotated = True
        self.rotation_pitch(rot[0])
        self.rotation_yaw(rot[1])
        self.rotation_roll(rot[2])

    def rotation_pitch(self, delta=0.0):
        self.rotated = True
        self.rot[0] += delta
        if self.rot[0] > TWO_PI or self.rot[0] < 0.0:
            self.rot[0] %= TWO_PI

    def rotation_yaw(self, delta=0.0):
        self.rotated = True
        self.rot[1] += delta
        if self.rot[1] > TWO_PI or self.rot[1] < 0.0:
            self.rot[1] %= TWO_PI

    def rotation_roll(self, delta=0.0):
        self.rotated = True
        self.rot[2] += delta
        if self.rot[2] > TWO_PI or self.rot[2] < 0.0:
            self.rot[2] %= TWO_PI

    # Scale
    def get_scale(self):
        return self.scale

    def set_scale(self, vScale):
        self.scaled = True
        self.scale[...] = vScale

    def set_scale_x(self, x):
        self.scaled = True
        self.scale[0] = x

    def set_scale_y(self, y):
        self.scaled = True
        self.scale[1] = y

    def set_scale_z(self, z):
        self.scaled = True
        self.scale[2] = z

    def scaling(self, vScale):
        self.scaled = True
        self.scale[...] = self.scale + vScale

    # update Transform
    def update_transform(self, update_inverse_matrix=False, force_update=False):
        prev_updated = self.updated
        self.updated = False

        if self.moved and any(self.prev_Pos != self.pos) or force_update:
            self.prev_Pos[...] = self.pos
            set_translate_matrix(self.translateMatrix, self.pos[0], self.pos[1], self.pos[2])
            self.moved = False
            self.updated = True

        if self.rotated and any(self.prev_Rot != self.rot) or force_update:
            self.prev_Rot[...] = self.rot
            self.rotated = False
            self.updated = True

            # Matrix Rotation - faster
            matrix_rotation(self.rotationMatrix, *self.rot)
            matrix_to_vectors(self.rotationMatrix, self.left, self.up, self.front)

            # Euler Rotation - slow
            # p = get_rotation_matrix_x(self.rot[0])
            # y = get_rotation_matrix_y(self.rot[1])
            # r = get_rotation_matrix_z(self.rot[2])
            # self.rotationMatrix = np.dot(p, np.dot(y, r))
            # matrix_to_vectors(self.rotationMatrix, self.right, self.up, self.front)

            # Quaternion Rotation - slower
            # euler_to_quaternion(*self.rot, self.quat)
            # quaternion_to_matrix(self.quat, self.rotationMatrix)
            # matrix_to_vectors(self.rotationMatrix, self.right, self.up, self.front)

        if self.scaled and any(self.prev_Scale != self.scale) or force_update:
            self.prev_Scale[...] = self.scale
            set_scale_matrix(self.scaleMatrix, self.scale[0], self.scale[1], self.scale[2])
            self.scaled = False
            self.updated = True

        if prev_updated or self.updated:
            self.prev_matrix[...] = self.matrix
            if update_inverse_matrix:
                self.prev_inverse_matrix[...] = self.inverse_matrix

        if self.updated:
            self.matrix[...] = dot_arrays(self.local, self.scaleMatrix, self.rotationMatrix, self.translateMatrix)
            if update_inverse_matrix:
                self.inverse_matrix[...] = np.linalg.inv(self.matrix)
        return self.updated

    def get_transform_infos(self):
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
