import numpy as np

from .Transform import *


class TransformObject:
    def __init__(self, local=None):
        self.local = local if local is not None else Matrix4()

        self.updated = True

        self.left = WORLD_LEFT.copy()
        self.up = WORLD_UP.copy()
        self.front = WORLD_FRONT.copy()

        self.pos = Float3()
        self.rot = Float3()
        self.euler_to_quat = QUATERNION_IDENTITY.copy()
        self.quat = QUATERNION_IDENTITY.copy()
        self.final_rotation = QUATERNION_IDENTITY.copy()
        self.scale = Float3(1, 1, 1)

        self.prev_pos = Float3()
        self.prev_Rot = Float3()
        self.prev_quat = QUATERNION_IDENTITY.copy()
        self.prev_final_rotation = QUATERNION_IDENTITY.copy()
        self.prev_Scale = Float3(1, 1, 1)

        self.prev_pos_store = Float3()

        self.quaternionMatrix = Matrix4()
        self.eulerMatrix = Matrix4()
        self.rotationMatrix = Matrix4()

        self.matrix = Matrix4()
        self.inverse_matrix = Matrix4()

        self.prev_matrix = Matrix4()
        self.prev_inverse_matrix = Matrix4()

        self.update_transform(True)

    def reset_transform(self):
        self.updated = True
        self.set_pos(Float3())
        self.set_rotation(Float3())
        self.set_quaternion(QUATERNION_IDENTITY)
        self.set_final_rotation(QUATERNION_IDENTITY)
        self.set_scale(Float3(1, 1, 1))
        self.update_transform(True)

    def clone(self, other_transform):
        self.set_pos(other_transform.get_pos())
        self.set_rotation(other_transform.get_rotation())
        self.set_quaternion(other_transform.get_quaternion())
        self.set_final_rotation(other_transform.get_final_rotation())
        self.set_scale(other_transform.get_scale())
        self.update_transform(True)

    # Translate
    def get_pos(self):
        return self.pos

    def get_prev_pos(self):
        return self.prev_pos_store

    def get_pos_x(self):
        return self.pos[0]

    def get_pos_y(self):
        return self.pos[1]

    def get_pos_z(self):
        return self.pos[2]

    def set_pos(self, pos):
        self.pos[...] = pos

    def set_prev_pos(self, prev_pos):
        self.prev_pos[...] = prev_pos

    def set_pos_x(self, x):
        self.pos[0] = x

    def set_pos_y(self, y):
        self.pos[1] = y

    def set_pos_z(self, z):
        self.pos[2] = z

    def move(self, pos):
        self.pos[...] = self.pos + pos

    def move_front(self, pos):
        self.pos[...] = self.pos + self.front * pos

    def move_left(self, pos):
        self.pos[...] = self.pos + self.left * pos

    def move_up(self, pos):
        self.pos[...] = self.pos + self.up * pos

    def move_x(self, pos_x):
        self.pos[0] += pos_x

    def move_y(self, pos_y):
        self.pos[1] += pos_y

    def move_z(self, pos_z):
        self.pos[2] += pos_z

    # Rotation
    def get_rotation(self):
        return self.rot

    def get_pitch(self):
        return self.rot[0]

    def get_yaw(self):
        return self.rot[1]

    def get_roll(self):
        return self.rot[2]

    def set_rotation(self, rot):
        self.rot[...] = rot

    def set_pitch(self, pitch):
        if pitch > TWO_PI or pitch < 0.0:
            pitch %= TWO_PI
        self.rot[0] = pitch

    def set_yaw(self, yaw):
        if yaw > TWO_PI or yaw < 0.0:
            yaw %= TWO_PI
        self.rot[1] = yaw

    def set_roll(self, roll):
        if roll > TWO_PI or roll < 0.0:
            roll %= TWO_PI
        self.rot[2] = roll

    def rotation(self, rot):
        self.rotation_pitch(rot[0])
        self.rotation_yaw(rot[1])
        self.rotation_roll(rot[2])

    def rotation_pitch(self, delta=0.0):
        self.rot[0] += delta
        if self.rot[0] > TWO_PI or self.rot[0] < 0.0:
            self.rot[0] %= TWO_PI

    def rotation_yaw(self, delta=0.0):
        self.rot[1] += delta
        if self.rot[1] > TWO_PI or self.rot[1] < 0.0:
            self.rot[1] %= TWO_PI

    def rotation_roll(self, delta=0.0):
        self.rot[2] += delta
        if self.rot[2] > TWO_PI or self.rot[2] < 0.0:
            self.rot[2] %= TWO_PI

    # Quaternion
    def get_final_rotation(self):
        return self.final_rotation

    def set_final_rotation(self, quat):
        self.final_rotation[...] = quat

    def get_quaternion(self):
        return self.quat

    def set_quaternion(self, quat):
        self.quat[...] = quat

    def axis_rotation(self, axis, radian):
        self.multiply_quaternion(axis_rotation(axis, radian))

    def multiply_quaternion(self, quat):
        self.quat[...] = muliply_quaternion(quat, self.quat)

    def normalize_quaternion(self):
        self.quat[...] = normalize(self.quat)

    def euler_to_quaternion(self):
        euler_to_quaternion(*self.rot, self.quat)

    # Scale
    def get_scale(self):
        return self.scale

    def get_scale_x(self):
        return self.scale[0]

    def get_scale_y(self):
        return self.scale[1]

    def get_scale_z(self):
        return self.scale[2]

    def set_scale(self, scale):
        self.scale[...] = scale

    def set_scale_x(self, x):
        self.scale[0] = x

    def set_scale_y(self, y):
        self.scale[1] = y

    def set_scale_z(self, z):
        self.scale[2] = z

    def scale_xyz(self, scale):
        self.scale_x(scale[0])
        self.scale_y(scale[1])
        self.scale_z(scale[2])

    def scale_x(self, x):
        self.scale[0] += x

    def scale_y(self, y):
        self.scale[1] += y

    def scale_z(self, z):
        self.scale[2] += z

    def scaling(self, scale):
        self.scale[...] = self.scale + scale

    def matrix_to_vectors(self):
        matrix_to_vectors(self.rotationMatrix, self.left, self.up, self.front, do_normalize=True)

    # update Transform
    def update_transform(self, update_inverse_matrix=False, force_update=False):
        prev_updated = self.updated
        self.updated = False
        rotation_update = False

        if any(self.prev_pos != self.pos) or force_update:
            self.prev_pos_store[...] = self.prev_pos
            self.prev_pos[...] = self.pos
            self.updated = True

        # Quaternion Rotation
        if any(self.prev_quat != self.quat) or force_update:
            self.prev_quat[...] = self.quat
            self.updated = True
            rotation_update = True
            quaternion_to_matrix(self.quat, self.quaternionMatrix)

        # Euler Roation
        if any(self.prev_Rot != self.rot) or force_update:
            self.prev_Rot[...] = self.rot
            self.updated = True
            rotation_update = True
            matrix_rotation(self.eulerMatrix, *self.rot)

        if rotation_update:
            self.rotationMatrix[...] = np.dot(self.eulerMatrix, self.quaternionMatrix)
            self.matrix_to_vectors()

        if any(self.prev_Scale != self.scale) or force_update:
            self.prev_Scale[...] = self.scale
            self.updated = True

        if prev_updated or self.updated:
            self.prev_matrix[...] = self.matrix
            if update_inverse_matrix:
                self.prev_inverse_matrix[...] = self.inverse_matrix

        if self.updated:
            self.matrix[...] = self.local
            transform_matrix(self.matrix, self.pos, self.rotationMatrix, self.scale)

            if update_inverse_matrix:
                # self.inverse_matrix[...] = np.linalg.inv(self.matrix)
                self.inverse_matrix[...] = self.local
                inverse_transform_matrix(self.inverse_matrix, self.pos, self.rotationMatrix, self.scale)

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
