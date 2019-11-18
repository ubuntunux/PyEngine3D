import os
import traceback

import numpy as np
from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.OpenGLContext import InstanceBuffer
from PyEngine3D.Utilities import *


class SplinePoint:
    def __init__(self, position=None, control_point=None):
        self.position = position if position is not None else Float3(0.0)
        self.control_point = control_point if control_point is not None else Float3(0.0)


class Spline3D:
    def __init__(self, spline_points, color=None, width=1.0):
        self.spline_points = spline_points
        self.color = color.copy() if color is not None else Float4(1.0, 1.0, 1.0, 1.0)
        self.width = width
        self.resampling_positions = np.zeros(0, dtype=(np.float32, 3))

    def resampling(self, resample_count=128):
        point_count = len(self.spline_points)
        segment_count = point_count - 1
        if segment_count < 1:
            return
        self.resampling_positions = np.zeros(resample_count, dtype=(np.float32, 3))

        index = 0
        resample_pos = 0.0
        resample_step = 1.0 / resample_count
        while resample_pos <= 1.0 and index < resample_count:
            t = resample_pos * segment_count
            if t == 1.0:
                point_index = min(point_count - 2, int(resample_pos * segment_count) - 1)
            else:
                t %= 1.0
                point_index = min(point_count - 2, int(resample_pos * segment_count))

            next_point_index = point_index + 1
            point = self.spline_points[point_index]
            next_point = self.spline_points[next_point_index]

            self.resampling_positions[index][...] = getCubicBezierCurvePoint(
                point.position,
                point.position + point.control_point,
                next_point.position - next_point.control_point,
                next_point.position,
                t
            )

            resample_pos += resample_step
            index += 1
