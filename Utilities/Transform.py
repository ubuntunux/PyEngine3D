#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Very simple transformation library that is needed for some examples.
original - http://www.labri.fr/perso/nrougier/teaching/opengl/#the-hard-way-opengl
"""

import math
import numpy as np

PI = math.pi
TWO_PI = 2.0 * math.pi

Float = lambda x=0.0: np.float32(x)
Float2 = lambda x=0.0, y=0.0: np.array([x, y], dtype=np.float32)
Float3 = lambda x=0.0, y=0.0, z=0.0: np.array([x, y, z], dtype=np.float32)
Float4 = lambda x=0.0, y=0.0, z=0.0, w=0.0: np.array([x, y, z, w], dtype=np.float32)
Identity = lambda: np.eye(4, dtype=np.float32)

FLOAT_ZERO = Float(0.0)
WORLD_RIGHT = Float3(1.0, 0.0, 0.0)
WORLD_UP = Float3(0.0, 1.0, 0.0)
WORLD_FRONT = Float3(0.0, 0.0, 1.0)

def transform(m, v):
    return np.asarray(m * np.asmatrix(v).T)[:, 0]


def magnitude(v):
    return math.sqrt(np.sum(v ** 2))


def normalize(v):
    m = magnitude(v)
    if m == 0:
        return v
    return v / m


def getTranslateMatrix(x, y, z):
    T = [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 1, 0],
         [x, y, z, 1]]
    return np.array(T, dtype=np.float32)


def translate(M, x, y, z):
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


def scale(M, x, y, z):
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


def rotateX(M, radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[1.0, 0.0, 0.0, 0.0],
         [0.0, cosT, sinT, 0.0],
         [0.0, -sinT, cosT, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    M[...] = np.dot(R, M)


def rotateY(M, radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[cosT, 0.0, -sinT, 0.0],
         [0.0, 1.0, 0.0, 0.0],
         [sinT, 0.0, cosT, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    M[...] = np.dot(R, M)


def rotateZ(M, radian):
    cosT = math.cos(radian)
    sinT = math.sin(radian)
    R = np.array(
        [[cosT, sinT, 0.0, 0.0],
         [-sinT, cosT, 0.0, 0.0],
         [0.0, 0.0, 1.0, 0.0],
         [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
    M[...] = np.dot(R, M)


def rotate(M, radian, x, y, z):
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


def lookat(eye, target, up):
    F = target[:3] - eye[:3]
    f = normalize(F)
    U = normalize(up[:3])
    s = np.cross(f, U)
    u = np.cross(s, f)
    M = np.eye(4, dtype=np.float32)
    M[:3, :3] = np.vstack([s, u, -f])
    T = getTranslateMatrix(*(-eye))
    return M * T


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


def frustum(left, right, bottom, top, znear, zfar):
    assert (right != left)
    assert (bottom != top)
    assert (znear != zfar)

    M = np.eye(4, dtype=np.float32)
    M[0, 0] = +2.0 * znear / (right - left)
    M[2, 0] = (right + left) / (right - left)
    M[1, 1] = +2.0 * znear / (top - bottom)
    M[3, 1] = (top + bottom) / (top - bottom)
    M[2, 2] = -(zfar + znear) / (zfar - znear)
    M[3, 2] = -2.0 * znear * zfar / (zfar - znear)
    M[2, 3] = -1.0
    return M


def perspective(fovy, aspect, znear, zfar):
    assert (znear != zfar)
    h = np.tan(fovy / 360.0 * np.pi) * znear
    w = h * aspect
    return frustum(-w, w, -h, h, znear, zfar)
