import os
import traceback
import copy

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


class SplineData:
    default_spline_points = [
        SplinePoint(Float3(0.0, 0.0, 0.0), Float3(1.0, 0.0, 0.0)),
        SplinePoint(Float3(4.0, 2.0, 0.0), Float3(1.0, 0.0, 0.0))
    ]

    def __init__(self, name, **data):
        self.name = name
        self.spline_points = data.get('spline_points', copy.deepcopy(self.default_spline_points))
        self.color = Float4(*data.get('color', [1.0, 1.0, 1.0, 1.0]))
        self.width = data.get('width', 1.0)
        self.resample_count = data.get('resampling_count', 128)
        self.resampling_positions = np.zeros(0, dtype=(np.float32, 3))
        self.resampling(self.resample_count)
        self.attributes = Attributes()

    def get_attribute(self):
        save_data = self.get_save_data()
        attribute_names = list(save_data.keys())
        attribute_names.sort()

        for attribute_name in attribute_names:
            self.attributes.set_attribute(attribute_name, save_data[attribute_name])
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        # print("SplineData", attribute_name, attribute_value, parent_info, attribute_index)
        if 'resample_count' == attribute_name:
            self.resampling(attribute_value)
        elif 'color' == attribute_name:
            self.color = Float4(*attribute_value)
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)

    def get_save_data(self):
        save_data = dict(
            name=self.name,
            spline_points=[(spline_point.position.tolist(), spline_point.control_point.tolist()) for spline_point in self.spline_points],
            color=self.color.tolist(),
            width=self.width,
            resample_count=self.resample_count
        )
        return save_data

    def resampling(self, resample_count=128):
        self.resample_count = resample_count
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


class Spline3D:
    def __init__(self, **spline_data):
        self.name = spline_data.get('name', 'spline')
        self.transform = TransformObject()
        self.transform.set_pos(spline_data.get('pos', [0, 0, 0]))
        self.transform.set_rotation(spline_data.get('rot', [0, 0, 0]))
        self.transform.set_scale(spline_data.get('scale', [1, 1, 1]))
        self.spline_data = spline_data.get('spline_data')
        self.attributes = Attributes()

    def get_attribute(self):
        save_data = self.get_save_data()
        attribute_names = list(save_data.keys())
        attribute_names.sort()

        for attribute_name in attribute_names:
            self.attributes.set_attribute(attribute_name, save_data[attribute_name])
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        if 'spline_data' == attribute_name:
            spline_data = CoreManager.instance().resource_manager.get_spline(attribute_value)
            if spline_data is not None:
                self.spline_data = spline_data
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)

    def get_save_data(self):
        save_data = dict(
            name=self.name,
            spline_data=self.spline_data.name if self.spline_data is not None else '',
            pos=self.transform.pos.tolist(),
            rot=self.transform.rot.tolist(),
            scale=self.transform.scale.tolist()
        )
        return save_data

    def update(self, dt):
        self.transform.update_transform()


