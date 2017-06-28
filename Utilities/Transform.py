#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Very simple transformation library that is needed for some examples.
original - http://www.labri.fr/perso/nrougier/teaching/opengl/#the-hard-way-opengl
quaternion - https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles

This implementation uses row vectors and matrices are written in a row-major order.

"""

import math
import numpy as np

HALF_PI = math.pi * 0.5
PI = math.pi
TWO_PI = math.pi * 2.0
FLOAT_ZERO = np.float32(0.0)
FLOAT2_ZERO = np.array([0.0, 0.0], dtype=np.float32)
FLOAT3_ZERO = np.array([0.0, 0.0, 0.0], dtype=np.float32)
FLOAT4_ZERO = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
MATRIX3_IDENTITY = np.eye(3, dtype=np.float32)
MATRIX4_IDENTITY = np.eye(4, dtype=np.float32)
WORLD_RIGHT = np.array([1.0, 0.0, 0.0], dtype=np.float32)
WORLD_UP = np.array([0.0, 1.0, 0.0], dtype=np.float32)
WORLD_FRONT = np.array([0.0, 0.0, 1.0], dtype=np.float32)


def Float(x=0.0):
    return np.float32(x)


def Float2(x=0.0, y=0.0):
    return np.array([x, y], dtype=np.float32)


def Float3(x=0.0, y=0.0, z=0.0):
    return np.array([x, y, z], dtype=np.float32)


def Float4(x=0.0, y=0.0, z=0.0, w=0.0):
    return np.array([x, y, z, w], dtype=np.float32)


def Matrix3():
    return np.eye(3, dtype=np.float32)


def Matrix4():
    return np.eye(4, dtype=np.float32)


def transform(m, v):
    return np.asarray(m * np.asmatrix(v).T)[:, 0]


def magnitude(v):
    return math.sqrt(np.sum(v ** 2))


def normalize(v):
    m = magnitude(v)
    if m == 0:
        return v
    return v / m


def euler_to_matrix(pitch, yaw, roll, rotationMatrix):
    '''
    create front vector
    right = cross(world_up, front)
    up - cross(right, front)
    conversion vector to matrix
    '''
    pass


def matrix_rotation(rx, ry, rz, rotationMatrix):
    ch = math.cos(ry)
    sh = math.sin(ry)
    ca = math.cos(rz)
    sa = math.sin(rz)
    cb = math.cos(rx)
    sb = math.sin(rx)

    rotationMatrix[:, 0] = [ch*ca, sh*sb - ch*sa*cb, ch*sa*sb + sh*cb, 0.0]
    rotationMatrix[:, 1] = [sa, ca*cb, -ca*sb, 0.0]
    rotationMatrix[:, 2] = [-sh*ca, sh*sa*cb + ch*sb, -sh*sa*sb + ch*cb, 0.0]


def matrix_to_vectors(rotationMatrix, axis_x, axis_y, axis_z):
    axis_x[:] = rotationMatrix[0, 0:3]
    axis_y[:] = rotationMatrix[1, 0:3]
    axis_z[:] = rotationMatrix[2, 0:3]


def get_quaternion(axis, radian):
    angle = radian * 0.5
    s = math.sin(angle)
    return Float4(math.cos(angle), axis[0]*s, axis[1]*s, axis[2]*s)


def muliply_quaternion(quaternion1, quaternion2):
    x = quaternion1[1]
    y = quaternion1[2]
    z = quaternion1[3]
    w = quaternion1[0]
    num4 = quaternion2[1]
    num3 = quaternion2[2]
    num2 = quaternion2[3]
    num = quaternion2[0]
    num12 = (y * num2) - (z * num3)
    num11 = (z * num4) - (x * num2)
    num10 = (x * num3) - (y * num4)
    num9 = ((x * num4) + (y * num3)) + (z * num2)
    qX = ((x * num) + (num4 * w)) + num12
    qY = ((y * num) + (num3 * w)) + num11
    qZ = ((z * num) + (num2 * w)) + num10
    qW = (w * num) - num9
    return Float4(qW, qX, qY, qZ)


def vector_multiply_quaternion(vector, quaternion):
    qv = Float3(quaternion[1], quaternion[2], quaternion[3])
    qw = quaternion[0]
    u = np.cross(vector, qv)
    return vector + u * 2.0 * qw + np.cross(qv, u) * 2.0


def euler_to_quaternion(rx, ry, rz, quat):
    t0 = math.cos(rz * 0.5)
    t1 = math.sin(rz * 0.5)
    t2 = math.cos(rx * 0.5)
    t3 = math.sin(rx * 0.5)
    t4 = math.cos(ry * 0.5)
    t5 = math.sin(ry * 0.5)
    t0t2 = t0 * t2
    t0t3 = t0 * t3
    t1t2 = t1 * t2
    t1t3 = t1 * t3
    qw = t0t2 * t4 + t1t3 * t5
    qx = t0t3 * t4 - t1t2 * t5
    qy = t0t2 * t5 + t1t3 * t4
    qz = t1t2 * t4 - t0t3 * t5
    n = 1.0 / math.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
    quat[0] = qw * n
    quat[1] = qx * n
    quat[2] = qy * n
    quat[3] = qz * n


def quaternion_to_matrix(quat, rotationMatrix):
    qw, qx, qy, qz = quat[:]
    # inhomogeneous expression
    qxqx = qx * qx * 2.0
    qxqy = qx * qy * 2.0
    qxqz = qx * qz * 2.0
    qxqw = qx * qw * 2.0
    qyqy = qy * qy * 2.0
    qyqz = qy * qz * 2.0
    qyqw = qy * qw * 2.0
    qzqw = qz * qw * 2.0
    qzqz = qz * qz * 2.0
    rotationMatrix[0, :] = [1.0 - qyqy - qzqz, qxqy + qzqw, qxqz - qyqw, 0.0]
    rotationMatrix[1, :] = [qxqy - qzqw, 1.0 - qxqx - qzqz, qyqz + qxqw, 0.0]
    rotationMatrix[2, :] = [qxqz + qyqw, qyqz - qxqw, 1.0 - qxqx - qyqy, 0.0]
    rotationMatrix[3, :] = [0.0, 0.0, 0.0, 1.0]
    '''
    # homogeneous expression
    qxqx = qx * qx
    qxqy = qx * qy * 2.0
    qxqz = qx * qz * 2.0
    qxqw = qx * qw * 2.0
    qyqy = qy * qy
    qyqz = qy * qz * 2.0
    qyqw = qy * qw * 2.0
    qzqw = qz * qw * 2.0
    qzqz = qz * qz
    qwqw = qw * qw
    rotationMatrix[0, :] = [qwqw + qxqx - qyqy - qzqz, qxqy + qzqw, qxqz - qyqw, 0.0]
    rotationMatrix[1, :] = [qxqy - qzqw, qwqw - qxqx + qyqy - qzqz, qyqz + qxqw, 0.0]
    rotationMatrix[2, :] = [qxqz + qyqw, qyqz - qxqw, qwqw - qxqx - qyqy + qzqz, 0.0]
    rotationMatrix[3, :] = [0.0, 0.0, 0.0, 1.0]
    '''


def slerp(quaternion1, quaternion2, amount):
    num = amount
    num2 = 0.0
    num3 = 0.0
    num4 = np.dot(quaternion1, quaternion2)
    flag = False
    if num4 < 0.0:
        flag = True
        num4 = -num4
    if num4 > 0.999999:
        num3 = 1.0 - num
        num2 = -num if flag else num
    else:
        num5 = math.acos(num4)
        num6 = 1.0 / math.sin(num5)
        num3 = math.sin((1.0 - num) * num5) * num6
        num2 = (-math.sin(num * num5) * num6) if flag else (math.sin(num * num5) * num6)
    return (num3 * quaternion1) + (num2 * quaternion2)


def getTranslateMatrix(x, y, z):
    T = [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 1, 0],
         [x, y, z, 1]]
    return np.array(T, dtype=np.float32)


def matrix_translate(M, x, y, z):
    T = [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 1, 0],
         [x, y, z, 1]]
    T = np.array(T, dtype=np.float32)
    M[...] = np.dot(T, M)


def getScaleMatrix(x, y, z):
    S = [[x, 0, 0, 0],
         [0, y, 0, 0],
         [0, 0, z, 0],
         [0, 0, 0, 1]]
    return np.array(S, dtype=np.float32)


def matrix_scale(M, x, y, z):
    S = [[x, 0, 0, 0],
         [0, y, 0, 0],
         [0, 0, z, 0],
         [0, 0, 0, 1]]
    S = np.array(S, dtype=np.float32)
    M[...] = np.dot(S, M)


def getRotationMatrixX(radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[1.0, 0.0, 0.0, 0.0],
         [0.0, cosT, sinT, 0.0],
         [0.0, -sinT, cosT, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    return R


def getRotationMatrixY(radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[cosT, 0.0, -sinT, 0.0],
         [0.0, 1.0, 0.0, 0.0],
         [sinT, 0.0, cosT, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    return R


def getRotationMatrixZ(radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[cosT, sinT, 0.0, 0.0],
         [-sinT, cosT, 0.0, 0.0],
         [0.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    return R


def matrix_rotateX(M, radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[1.0, 0.0, 0.0, 0.0],
         [0.0, cosT, sinT, 0.0],
         [0.0, -sinT, cosT, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    M[...] = np.dot(R, M)


def matrix_rotateY(M, radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[cosT, 0.0, -sinT, 0.0],
         [0.0, 1.0, 0.0, 0.0],
         [sinT, 0.0, cosT, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    M[...] = np.dot(R, M)


def matrix_rotateZ(M, radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[cosT, sinT, 0.0, 0.0],
         [-sinT, cosT, 0.0, 0.0],
         [0.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    M[...] = np.dot(R, M)


def matrix_rotate(M, radian, x, y, z):
    c, s = math.cos(radian), math.sin(radian)
    n = math.sqrt(x * x + y * y + z * z)
    x /= n
    y /= n
    z /= n
    cx, cy, cz = (1 - c) * x, (1 - c) * y, (1 - c) * z
    R = np.array([[cx * x + c, cy * x - z * s, cz * x + y * s, 0],
                  [cx * y + z * s, cy * y + c, cz * y - x * s, 0],
                  [cx * z - y * s, cy * z + x * s, cz * z + c, 0],
                  [0, 0, 0, 1]]).T
    M[...] = np.dot(R, M)


def lookat(matrix, eye, target, up):
    f = normalize(target - eye)
    s = np.cross(f, up)
    u = np.cross(s, f)
    matrix[0, 0:3] = s
    matrix[1, 0:3] = u
    matrix[2, 0:3] = -f
    matrix[3, 0:3] = [-np.dot(s, eye), -np.dot(u, eye), -np.dot(f, eye)]


def ortho(left, right, bottom, top, znear, zfar):
    assert (right != left)
    assert (bottom != top)
    assert (znear != zfar)

    M = np.zeros((4, 4), dtype=np.float32)
    M[0, 0] = +2.0 / (right - left)
    M[3, 0] = -(right + left) / float(right - left)
    M[1, 1] = +2.0 / (top - bottom)
    M[3, 1] = -(top + bottom) / float(top - bottom)
    M[2, 2] = -2.0 / (zfar - znear)
    M[3, 2] = -(zfar + znear) / float(zfar - znear)
    M[3, 3] = 1.0
    return M


def perspective(fovy, aspect, znear, zfar):
    assert (znear != zfar)
    # common equation
    h = np.tan(fovy / 360.0 * np.pi) * znear
    w = h * aspect
    left = -w
    right = w
    top = h
    bottom = -h

    M = Matrix4()
    M[0, :] = [2.0 * znear / (right - left), 0.0, 0.0, 0.0]
    M[1, :] = [0.0, 2.0 * znear / (top - bottom), 0.0, 0.0]
    M[2, :] = [(right + left) / (right - left), (top + bottom) / (top - bottom), -(zfar + znear) / (zfar - znear), -1.0]
    M[3, :] = [0.0, 0.0, -2.0 * znear * zfar / (zfar - znear), 0.0]
    return M


def compute_tangent(positions, texcoords, normals, indices):
    tangents = np.array([0.0, 0.0, 0.0] * len(normals), dtype=np.float32).reshape(len(normals), 3)
    # binormals = np.array([0.0, 0.0, 0.0] * len(normals), dtype=np.float32).reshape(len(normals), 3)

    for i in range(0, len(indices), 3):
        i1, i2, i3 = indices[i:i + 3]
        deltaPos2 = positions[i2] - positions[i1]
        deltaPos3 = positions[i3] - positions[i1]
        deltaUV2 = texcoords[i2] - texcoords[i1]
        deltaUV3 = texcoords[i3] - texcoords[i1]
        r = (deltaUV2[0] * deltaUV3[1] - deltaUV2[1] * deltaUV3[0])
        r = 1.0 / r if r != 0.0 else 0.0

        tangent = (deltaPos2 * deltaUV3[1] - deltaPos3 * deltaUV2[1]) * r
        tangent = normalize(tangent)
        # binormal = (deltaPos3 * deltaUV2[0]   - deltaPos2 * deltaUV3[0]) * r
        # binormal = normalize(binormal)

        tangents[indices[i]] = tangent
        tangents[indices[i + 1]] = tangent
        tangents[indices[i + 2]] = tangent
        # binormals[indices[i]] = binormal
        # binormals[indices[i+1]] = binormal
        # binormals[indices[i+2]] = binormal
    # return tangents, binormals
    return tangents
