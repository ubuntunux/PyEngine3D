#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Very simple transformation library that is needed for some examples.
original - http://www.labri.fr/perso/nrougier/teaching/opengl/#the-hard-way-opengl
quaternion - https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles

This implementation uses row vectors and matrices are written in a row-major order.

reference - http://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/index.htm
"""

import math
from functools import reduce

import numpy as np


HALF_PI = math.pi * 0.5
PI = math.pi
TWO_PI = math.pi * 2.0
FLOAT32_MIN = np.finfo(np.float32).min
FLOAT32_MAX = np.finfo(np.float32).max
FLOAT_ZERO = np.float32(0.0)
FLOAT2_ZERO = np.zeros(2, dtype=np.float32)
FLOAT3_ZERO = np.zeros(3, dtype=np.float32)
FLOAT4_ZERO = np.zeros(4, dtype=np.float32)
INT_ZERO = np.int32(0)
INT2_ZERO = np.zeros(2, dtype=np.int32)
INT3_ZERO = np.zeros(3, dtype=np.int32)
INT4_ZERO = np.zeros(4, dtype=np.int32)
QUATERNION_IDENTITY = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
MATRIX3_IDENTITY = np.eye(3, dtype=np.float32)
MATRIX3x4_IDENTITY = np.eye(3, 4, dtype=np.float32)
MATRIX4_IDENTITY = np.eye(4, dtype=np.float32)
WORLD_LEFT = np.array([1.0, 0.0, 0.0], dtype=np.float32)
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


def length(v):
    return math.sqrt(np.sum(v * v))


def normalize(v):
    m = length(v)
    if m == 0:
        return v
    return v / m


def dot_arrays(*array_list):
    return reduce(np.dot, array_list)


def clamp_radian(r):
    return (r % TWO_PI) if (TWO_PI < r) or (r < 0.0) else r


def radian_to_degree(radian):
    return clamp_radian(radian) / TWO_PI * 360.0


# Checks if a matrix is a valid rotation matrix.
def is_rotation_matrix(R):
    Rt = np.transpose(R)
    shouldBeIdentity = np.dot(Rt, R)
    I = np.identity(3, dtype=R.dtype)
    n = np.linalg.norm(I - shouldBeIdentity)
    return n < 1e-6


def rotation_maxtrix_to_euler_angles(R, check_valid=False):
    if check_valid:
        assert (is_rotation_matrix(R))

    sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

    singular = sy < 1e-6

    if not singular:
        x = math.atan2(R[1, 2], R[2, 2])
        y = math.atan2(-R[0, 2], sy)
        z = math.atan2(R[0, 1], R[0, 0])
    else:
        x = math.atan2(-R[2, 1], R[1, 1])
        y = math.atan2(-R[0, 2], sy)
        z = 0

    return Float3(x, y, z)


def matrix_rotation(rotation_matrix, rx, ry, rz):
    ch = math.cos(ry)
    sh = math.sin(ry)
    ca = math.cos(rz)
    sa = math.sin(rz)
    cb = math.cos(rx)
    sb = math.sin(rx)

    rotation_matrix[:, 0] = [ch*ca, sh*sb - ch*sa*cb, ch*sa*sb + sh*cb, 0.0]
    rotation_matrix[:, 1] = [sa, ca*cb, -ca*sb, 0.0]
    rotation_matrix[:, 2] = [-sh*ca, sh*sa*cb + ch*sb, -sh*sa*sb + ch*cb, 0.0]


def matrix_to_vectors(rotation_matrix, axis_x, axis_y, axis_z, do_normalize=False):
    if do_normalize:
        rotation_matrix[0, 0:3] = normalize(rotation_matrix[0, 0:3])
        rotation_matrix[1, 0:3] = normalize(rotation_matrix[1, 0:3])
        rotation_matrix[2, 0:3] = normalize(rotation_matrix[2, 0:3])
    axis_x[:] = rotation_matrix[0, 0:3]
    axis_y[:] = rotation_matrix[1, 0:3]
    axis_z[:] = rotation_matrix[2, 0:3]


def getYawPitchRoll(m):
    pitch = arcsin(-m[2][1])
    threshold = 1e-8
    test = cos(pitch)
    if test < threshold:
        roll = math.arctan2(-m[1][0], m[0][0])
        yaw = 0.0
    else:
        roll = math.arctan2(m[0][1], m[1][1])
        yaw = math.arctan2(m[2][0], m[2][2])
    return yaw, pitch, roll


def axis_rotation(axis, radian):
    angle = radian * 0.5
    s = math.sin(angle)
    return Float4(math.cos(angle), axis[0]*s, axis[1]*s, axis[2]*s)


def muliply_quaternion(quaternion1, quaternion2):
    w1, x1, y1, z1 = quaternion1
    w2, x2, y2, z2 = quaternion2
    qX = (y1 * z2) - (z1 * y2)
    qY = (z1 * x2) - (x1 * z2)
    qZ = (x1 * y2) - (y1 * x2)
    qW = (x1 * x2) + (y1 * y2) + (z1 * z2)
    qX = (x1 * w2) + (x2 * w1) + qX
    qY = (y1 * w2) + (y2 * w1) + qY
    qZ = (z1 * w2) + (z2 * w1) + qZ
    qW = (w1 * w2) - qW
    return Float4(qW, qX, qY, qZ)


def muliply_quaternions(*quaternions):
    return reduce(muliply_quaternion, quaternions)


def vector_multiply_quaternion(vector, quaternion):
    u = np.cross(vector, quaternion[1:])
    return vector + u * 2.0 * quaternion[0] + np.cross(quaternion[1:], u) * 2.0


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


def matrix_to_quaternion(matrix):
    m00, m01, m02, m03 = matrix[0, :]
    m10, m11, m12, m13 = matrix[1, :]
    m20, m21, m22, m23 = matrix[2, :]

    tr = m00 + m11 + m22
    if tr > 0.0:
        S = math.sqrt(tr+1.0) * 2.0
        qw = 0.25 * S
        qx = (m12 - m21) / S
        qy = (m20 - m02) / S
        qz = (m01 - m10) / S
    elif m00 > m11 and m00 > m22:
        S = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        qw = (m12 - m21) / S
        qx = 0.25 * S
        qy = (m10 + m01) / S
        qz = (m20 + m02) / S
    elif m11 > m22:
        S = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        qw = (m20 - m02) / S
        qx = (m10 + m01) / S
        qy = 0.25 * S
        qz = (m21 + m12) / S
    else:
        S = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        qw = (m01 - m10) / S
        qx = (m20 + m02) / S
        qy = (m21 + m12) / S
        qz = 0.25 * S
    return normalize(Float4(qw, qx, qy, qz))


def quaternion_to_matrix(quat, rotation_matrix):
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
    rotation_matrix[0, :] = [1.0 - qyqy - qzqz, qxqy + qzqw, qxqz - qyqw, 0.0]
    rotation_matrix[1, :] = [qxqy - qzqw, 1.0 - qxqx - qzqz, qyqz + qxqw, 0.0]
    rotation_matrix[2, :] = [qxqz + qyqw, qyqz - qxqw, 1.0 - qxqx - qyqy, 0.0]
    rotation_matrix[3, :] = [0.0, 0.0, 0.0, 1.0]
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
    rotation_matrix[0, :] = [qwqw + qxqx - qyqy - qzqz, qxqy + qzqw, qxqz - qyqw, 0.0]
    rotation_matrix[1, :] = [qxqy - qzqw, qwqw - qxqx + qyqy - qzqz, qyqz + qxqw, 0.0]
    rotation_matrix[2, :] = [qxqz + qyqw, qyqz - qxqw, qwqw - qxqx - qyqy + qzqz, 0.0]
    rotation_matrix[3, :] = [0.0, 0.0, 0.0, 1.0]
    '''


def quaternion_to_euler(q):
    sqw = w * w
    sqx = x * x
    sqy = y * y
    sqz = z * z
    m = Matrix3()
    m[0][0] = sqx - sqy - sqz + sqw
    m[1][1] = -sqx + sqy - sqz + sqw
    m[2][2] = -sqx - sqy + sqz + sqw
    tmp1 = x * y
    tmp2 = z * w
    m[0][1] = 2.0 * (tmp1 + tmp2)
    m[1][0] = 2.0 * (tmp1 - tmp2)
    tmp1 = x * z
    tmp2 = y * w
    m[0][2] = 2.0 * (tmp1 - tmp2)
    m[2][0] = 2.0 * (tmp1 + tmp2)
    tmp1 = y * z
    tmp2 = x * w
    m[1][2] = 2.0 * (tmp1 + tmp2)
    m[2][1] = 2.0 * (tmp1 - tmp2)


def lerp(vector1, vector2, t):
    return vector1 * (1.0 - t) + vector2 * t


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


def set_identity_matrix(M):
    M[...] = [[1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]]


def get_translate_matrix(x, y, z):
    T = [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 1, 0],
         [x, y, z, 1]]
    return np.array(T, dtype=np.float32)


def set_translate_matrix(M, x, y, z):
    M[:] = [[1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [x, y, z, 1]]


def matrix_translate(M, x, y, z):
    M[3][0] += x
    M[3][1] += y
    M[3][2] += z


def get_scale_matrix(x, y, z):
    S = [[x, 0, 0, 0],
         [0, y, 0, 0],
         [0, 0, z, 0],
         [0, 0, 0, 1]]
    return np.array(S, dtype=np.float32)


def set_scale_matrix(M, x, y, z):
    M[:] = [[x, 0, 0, 0],
            [0, y, 0, 0],
            [0, 0, z, 0],
            [0, 0, 0, 1]]


def matrix_scale(M, x, y, z):
    M[0] *= x
    M[1] *= y
    M[2] *= z


def get_rotation_matrix_x(radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[1.0, 0.0, 0.0, 0.0],
         [0.0, cosT, sinT, 0.0],
         [0.0, -sinT, cosT, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    return R


def get_rotation_matrix_y(radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[cosT, 0.0, -sinT, 0.0],
         [0.0, 1.0, 0.0, 0.0],
         [sinT, 0.0, cosT, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    return R


def get_rotation_matrix_z(radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[cosT, sinT, 0.0, 0.0],
         [-sinT, cosT, 0.0, 0.0],
         [0.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    return R


def matrix_rotate_x(M, radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[1.0, 0.0, 0.0, 0.0],
         [0.0, cosT, sinT, 0.0],
         [0.0, -sinT, cosT, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    M[...] = np.dot(M, R)


def matrix_rotate_y(M, radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[cosT, 0.0, -sinT, 0.0],
         [0.0, 1.0, 0.0, 0.0],
         [sinT, 0.0, cosT, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    M[...] = np.dot(M, R)


def matrix_rotate_z(M, radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[cosT, sinT, 0.0, 0.0],
         [-sinT, cosT, 0.0, 0.0],
         [0.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    M[...] = np.dot(M, R)


def matrix_rotate_axis(M, radian, x, y, z):
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
    M[...] = np.dot(M, R)


def matrix_rotate(M, rx, ry, rz):
    R = MATRIX4_IDENTITY.copy()
    matrix_rotation(R, rx, ry, rz)
    M[...] = np.dot(M, R)


def swap_up_axis_matrix(matrix, transpose, isInverseMatrix, up_axis):
    if transpose:
        matrix = matrix.T
    if up_axis == 'Z_UP':
        if isInverseMatrix:
            return np.dot(get_rotation_matrix_x(HALF_PI), matrix)
        else:
            return np.dot(matrix, get_rotation_matrix_x(-HALF_PI))
    return matrix


def swap_matrix(matrix, transpose, up_axis):
    if transpose:
        matrix = matrix.T
    if up_axis == 'Z_UP':
        return np.array(
            [matrix[0, :].copy(),
             matrix[2, :].copy(),
             -matrix[1, :].copy(),
             matrix[3, :].copy()]
        )
    return matrix


def transform_matrix(M, translation, rotation_matrix, scale):
    matrix_scale(M, *scale)
    M[...] = np.dot(M, rotation_matrix)
    matrix_translate(M, *translation)


def inverse_transform_matrix(M, translation, rotation_matrix, scale):
    matrix_translate(M, *(-translation))
    M[...] = np.dot(M, rotation_matrix.T)
    if all(0.0 != scale):
        matrix_scale(M, *(1.0 / scale))


def extract_location(matrix):
    return Float3(matrix[3, 0], matrix[3, 1], matrix[3, 2])


def extract_rotation(matrix):
    scale = extract_scale(matrix)
    rotation = Matrix4()
    rotation[0, :] = matrix[0, :] / scale[0]
    rotation[1, :] = matrix[1, :] / scale[1]
    rotation[2, :] = matrix[2, :] / scale[2]
    return rotation


def extract_quaternion(matrix):
    return matrix_to_quaternion(extract_rotation(matrix))


def extract_scale(matrix):
    sX = np.linalg.norm(matrix[0, :])
    sY = np.linalg.norm(matrix[1, :])
    sZ = np.linalg.norm(matrix[2, :])
    return Float3(sX, sY, sZ)


def lookat(matrix, eye, target, up):
    f = normalize(target - eye)
    s = np.cross(f, up)
    u = np.cross(s, f)
    matrix[0, 0:3] = s
    matrix[1, 0:3] = u
    matrix[2, 0:3] = f
    matrix[3, 0:3] = [-np.dot(s, eye), -np.dot(u, eye), -np.dot(f, eye)]


def ortho(M, left, right, bottom, top, znear, zfar):
    M[0, 0] = 2.0 / (right - left)
    M[1, 1] = 2.0 / (top - bottom)
    M[2, 2] = -2.0 / (zfar - znear)
    M[3, 0] = -(right + left) / float(right - left)
    M[3, 1] = -(top + bottom) / float(top - bottom)
    M[3, 2] = -(zfar + znear) / float(zfar - znear)
    M[3, 3] = 1.0
    return M


def perspective(fovy, aspect, znear, zfar):
    if znear == zfar:
        znear = 0.0
        zfar = znear + 1000.0

    if fovy <= 0.0:
        fovy = 45.0

    height = np.tan((fovy * 0.5) / 180.0 * np.pi) * znear
    width = height * aspect
    depth = zfar - znear

    left = -width
    right = width
    top = height
    bottom = -height

    '''        
    M = Maxtrix4()
    M[0, :] = [2.0 * znear / (right - left), 0.0, 0.0, 0.0]
    M[1, :] = [0.0, 2.0 * znear / (top - bottom), 0.0, 0.0]
    M[2, :] = [(right + left) / (right - left), (top + bottom) / (top - bottom), -(zfar + znear) / (zfar - znear), -1.0]
    M[3, :] = [0.0, 0.0, -2.0 * znear * zfar / (zfar - znear), 0.0]
    '''

    # Compact version, it is assumed that x1 and x2 are the same.
    M = Matrix4()
    M[0, :] = [znear / width, 0.0, 0.0, 0.0]
    M[1, :] = [0.0, znear / height, 0.0, 0.0]
    M[2, :] = [0.0, 0.0, -(zfar + znear) / depth, -1.0]
    M[3, :] = [0.0, 0.0, -2.0 * znear * zfar / depth, 0.0]
    return M


def convert_triangulate(polygon, vcount, stride=1):
    indices_list = [polygon[i * stride:i * stride + stride] for i in range(int(len(polygon) / stride))]
    triangulated_list = []
    # first triangle
    triangulated_list += indices_list[0]
    triangulated_list += indices_list[1]
    triangulated_list += indices_list[2]
    t1 = indices_list[1]  # center of poylgon
    t2 = indices_list[2]
    for i in range(3, vcount):
        triangulated_list += t2
        triangulated_list += t1
        triangulated_list += indices_list[i]
        t2 = indices_list[i]


# http://jerome.jouvie.free.fr/opengl-tutorials/Lesson8.php
def compute_tangent(is_triangle_mode, positions, texcoords, normals, indices):
    """
    Note: This point can also be considered as the vector starting from the origin to pi.
    Writting this equation for the points p1, p2 and p3 give :
        p1 = u1 * T + v1 * B
        p2 = u2 * T + v2 * B
        p3 = u3 * T + v3 * B
    Texture/World space relation

    With equation manipulation (equation subtraction), we can write :
        p2 - p1 = (u2 - u1) * T + (v2 - v1) * B
        p3 - p1 = (u3 - u1) * T + (v3 - v1) * B

    By resolving this system :
        Equation of Tangent:
            (v3 - v1) * (p2 - p1) = (v3 - v1) * (u2 - u1) * T + (v3 - v1) * (v2 - v1) * B
            (v2 - v1) * (p3 - p1) = (v2 - v1) * (u3 - u1) * T + (v2 - v1) * (v3 - v1) * B

        Equation of Binormal:
            (u3 - u1) * (p2 - p1) = (u3 - u1) * (u2 - u1) * T + (u3 - u1) * (v2 - v1) * B
            (u2 - u1) * (p3 - p1) = (u2 - u1) * (u3 - u1) * T + (u2 - u1) * (v3 - v1) * B


    And we finally have the formula of T and B :
        T = ((v3 - v1) * (p2 - p1) - (v2 - v1) * (p3 - p1)) / ((u2 - u1) * (v3 - v1) - (u3 - u1) * (v2 - v1))
        B = ((u3 - u1) * (p2 - p1) - (u2 - u1) * (p3 - p1)) / -((u2 - u1) * (v3 - v1) - (u3 - u1) * (v2 - v1))

    Equation of N:
        N = cross(T, B)
    """

    tangents = np.array([[1.0, 0.0, 0.0], ] * len(normals), dtype=np.float32)
    # binormals = np.array([[0.0, 0.0, 1.0], ] * len(normals), dtype=np.float32)

    if is_triangle_mode:
        for i in range(0, len(indices), 3):
            i0, i1, i2 = indices[i:i + 3]
            deltaPos_0_1 = positions[i1] - positions[i0]
            deltaPos_0_2 = positions[i2] - positions[i0]
            deltaUV_0_1 = texcoords[i1] - texcoords[i0]
            deltaUV_0_2 = texcoords[i2] - texcoords[i0]
            r = deltaUV_0_1[0] * deltaUV_0_2[1] - deltaUV_0_1[1] * deltaUV_0_2[0]
            r = (1.0 / r) if r != 0.0 else 0.0

            tangent = (deltaPos_0_1 * deltaUV_0_2[1] - deltaPos_0_2 * deltaUV_0_1[1]) * r
            tangent = normalize(tangent)
            # binormal = (deltaPos_0_2 * deltaUV_0_1[0]   - deltaPos_0_1 * deltaUV_0_2[0]) * r
            # binormal = normalize(binormal)

            # invalid tangent
            if 0.0 == np.dot(tangent, tangent):
                avg_normal = normalize(normals[i0] + normals[i1] + normals[i2])
                tangent = np.cross(avg_normal, WORLD_UP)

            tangents[indices[i]] = tangent
            tangents[indices[i + 1]] = tangent
            tangents[indices[i + 2]] = tangent

            # binormals[indices[i]] = binormal
            # binormals[indices[i+1]] = binormal
            # binormals[indices[i+2]] = binormal
    else:
        for i in range(0, len(indices), 4):
            i0, i1, i2, i3 = indices[i:i + 4]
            deltaPos_0_1 = positions[i1] - positions[i0]
            deltaPos_0_2 = positions[i2] - positions[i0]
            deltaUV_0_1 = texcoords[i1] - texcoords[i0]
            deltaUV_0_2 = texcoords[i2] - texcoords[i0]
            r = deltaUV_0_1[0] * deltaUV_0_2[1] - deltaUV_0_1[1] * deltaUV_0_2[0]
            r = (1.0 / r) if r != 0.0 else 0.0

            tangent = (deltaPos_0_1 * deltaUV_0_2[1] - deltaPos_0_2 * deltaUV_0_1[1]) * r
            tangent = normalize(tangent)

            # invalid tangent
            if 0.0 == np.dot(tangent, tangent):
                avg_normal = normalize(normals[i0] + normals[i1] + normals[i2])
                tangent = np.cross(avg_normal, WORLD_UP)

            tangents[indices[i]] = tangent
            tangents[indices[i + 1]] = tangent
            tangents[indices[i + 2]] = tangent
            tangents[indices[i + 3]] = tangent
    # return tangents, binormals
    return tangents
