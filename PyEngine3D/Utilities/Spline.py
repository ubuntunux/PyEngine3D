import math
import numpy as np


def hermiteInterpolate(y0, y1, y2, y3, mu, tension=0.5):
    mu2 = mu * mu
    mu3 = mu2 * mu
    m0 = (y1 - y0) * tension
    m0 += (y2 - y1) * tension
    m1 = (y2 - y1) * tension
    m1 += (y3 - y2) * tension
    a0 = 2 * mu3 - 3 * mu2 + 1
    a1 = mu3 - 2 * mu2 + mu
    a2 = mu3 - mu2
    a3 = -2 * mu3 + 3 * mu2

    return a0 * y1 + a1 * m0 + a2 * m1 + a3 * y2


def getSplineSmoothValue(points, time):
    size = len(points)

    if time < 0.0:
        return points[0][1]
    elif 0.99 < time:
        return points[size-1][1]

    t0 = 0.0
    t1 = 0.01
    v0 = 0.0
    v1 = 0.0
    v2 = 0.0
    v3 = 0.0

    if 0.0 == time:
        t0 = 0.0
        t1 = points[1][0]
        v0 = points[0][1]
        v1 = points[0][1]
        v2 = points[1][1]
        if size <= 2:
            v3 = points[1][1]
        else:
            v3 = points[2][1]
    elif 1.0 == time:
        t0 = points[size-2][0]
        t1 = 1.0
        v1 = points[size-2][1]
        v2 = points[size-1][1]
        v3 = points[size-1][1]
        if 3 <= size:
            v0 = points[size-3][1]
        else:
            v0 = points[size-2][1]
    else:
        for i in range(1, size, 1):
            if time < points[i][0]:
                t0 = points[i-1][0]
                t1 = points[i][0]
                v1 = points[i-1][1]
                v2 = points[i][1]

                if i < 2:
                    v0 = v1
                else:
                    v0 = points[i-2][1]

                if (size - 1) <= i:
                    v3 = v2
                else:
                    v3 = points[i+1][1]
                break
    t = (time - t0) / (t1 - t0)
    return hermiteInterpolate(v0, v1, v2, v3, t, 0.5)


def catmullRom(v0, v1, v2, v3, t):
    t2 = t * t
    t3 = t2 * t

    p0 = -t3 + 2.0 * t2 - t
    p1 = 3.0 * t3 - 5.0 * t2 + 2.0
    p2 = -3.0 * t3 + 4.0 * t2 + t
    p3 = t3 - t2
    return (p0 * v0 + p1 * v1 + p2 * v2 + p3 * v3) * 0.5


def getQuadraticBezierCurvePoint(p0, c0, p1, t):
    inv_t = 1.0 - t
    return (inv_t * inv_t * p0) + (2.0 * t * inv_t * c0) + (t * t * p1)


def getCubicBezierCurvePoint(p0, c0, c1, p1, t):
    t2 = t * t
    inv_t = 1.0 - t
    return (inv_t * inv_t * inv_t * p0) + (3.0 * t * inv_t * inv_t * c0) + (3.0 * inv_t * t2 * c1) + t2 * t * p1
