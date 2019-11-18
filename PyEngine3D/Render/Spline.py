import os
import traceback

import numpy as np
from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.OpenGLContext import InstanceBuffer
from PyEngine3D.Utilities import *


class SplinePoint:
    def __init__(self, position, control_point):
        self.position = position
        self.control_point = control_point


class Spline3D:
    def __init__(self, spline_points, color=None, width=1.0):
        self.spline_points = spline_points
        self.color = color.copy() if color is not None else Float4(1.0, 1.0, 1.0, 1.0)
        self.width = width
        self.resampling_positions = []

    def resampling(self, resample_count=128):
        for i in range(resample_count):
            pass
