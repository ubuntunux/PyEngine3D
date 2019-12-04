import os
import traceback
import copy
import math

import numpy as np
from OpenGL.GL import *

from PyEngine3D.Common import logger, COMMAND
from PyEngine3D.App import CoreManager
from PyEngine3D.OpenGLContext import InstanceBuffer
from PyEngine3D.Utilities import *


class SplinePoint:
    def __init__(self, position=None, control_point=None, point_time=1.0):
        self.position = position if position is not None else Float3()
        self.control_point = control_point if control_point is not None else Float3()
        self.point_time = point_time

    def get_save_data(self):
        return dict(
            position=self.position.tolist(),
            control_point=self.control_point.tolist(),
            point_time=self.point_time
        )


class SplineData:
    default_spline_points = [
        SplinePoint(Float3(0.0, 0.0, 0.0), Float3(1.0, 0.0, 0.0), 0.0),
        SplinePoint(Float3(4.0, 2.0, 0.0), Float3(1.0, 0.0, 0.0), 1.0)
    ]

    def __init__(self, name, **data):
        self.name = name
        self.spline_points = data.get('spline_points', copy.deepcopy(self.default_spline_points))
        self.resample_count = data.get('resample_count', 128)
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

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        item_info = item_info_history[0]
        if 'resample_count' == attribute_name:
            self.resampling(attribute_value)
        elif 'spline_points' == item_info.attribute_name:
            spine_point_index = item_info_history[1].index
            spline_point_attribute_name = item_info_history[2].index
            spine_point = self.spline_points[spine_point_index]
            if 'position' == spline_point_attribute_name:
                spine_point.position[...] = attribute_value
            elif 'control_point' == spline_point_attribute_name:
                spine_point.control_point[...] = attribute_value
            elif 'point_time' == spline_point_attribute_name:
                spine_point.point_time = attribute_value
            self.resampling()
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)

    def add_spline_point(self):
        point_count = len(self.spline_points)
        if 1 == point_count:
            self.spline_points.append(copy.deepcopy(self.default_spline_points[-1]))
        elif 1 < point_count:
            point = self.spline_points[-1].position * 2.0 - self.spline_points[-2].position
            self.spline_points.append(SplinePoint(point, self.spline_points[-1].control_point.copy()))
        else:
            self.spline_points = copy.deepcopy(self.default_spline_points)
        self.resampling()

    def delete_spline_point(self, index):
        if len(self.spline_points) <= 2:
            return
        self.spline_points.pop(index)
        self.resampling()

    def refresh_attribute_info(self):
        CoreManager.instance().send(COMMAND.TRANS_RESOURCE_ATTRIBUTE, self.get_attribute())

    def add_component(self, attribute_name, parent_info, attribute_index):
        if 'spline_points' == attribute_name:
            self.add_spline_point()
            self.refresh_attribute_info()

    def delete_component(self, attribute_name, parent_info, attribute_index):
        if parent_info is not None and 'spline_points' == parent_info.attribute_name:
            self.delete_spline_point(attribute_index)
            self.refresh_attribute_info()

    def get_save_data(self):
        save_data = dict(
            name=self.name,
            spline_points=[spline_point.get_save_data() for spline_point in self.spline_points],
            resample_count=self.resample_count
        )
        return save_data

    def get_resampling_position(self, ratio):
        resample_index = float(self.resample_count - 1) * min(1.0, max(0.0, ratio))
        index_min = math.floor(resample_index)
        index_max = math.ceil(resample_index)
        factor = resample_index - index_min
        return lerp(self.resampling_positions[index_min], self.resampling_positions[index_max], factor)

    def resampling(self, resample_count=None):
        if resample_count is not None:
            self.resample_count = max(1, resample_count)

        self.resampling_positions = np.zeros(self.resample_count, dtype=(np.float32, 3))

        point_count = len(self.spline_points)
        if point_count == 0:
            return
        elif point_count == 1:
            spline_point = self.spline_points[0]
            for i in range(self.resample_count):
                self.resampling_positions[i][...] = spline_point.position
        # 가장 첫번째 point의 시간은 제외
        total_time = sum([self.spline_points[i].point_time for i in range(1, len(self.spline_points), 1)])
        key_frames = [spline_point.point_time for spline_point in self.spline_points]
        key_frames[0] = 0.0
        key_frames = [sum(key_frames[:i+1]) for i in range(len(key_frames))]

        point_index = 0
        resample_pos = 0.0
        resample_step = total_time / (self.resample_count - 1)
        for i in range(self.resample_count):
            while True:
                if key_frames[point_index] <= resample_pos <= key_frames[point_index + 1]:
                    break
                if (point_count - 2) <= point_index:
                    break
                point_index += 1

            spline_point = self.spline_points[point_index]
            next_spline_point = self.spline_points[point_index + 1]
            time_range = key_frames[point_index + 1] - key_frames[point_index]
            t = min(1.0, max(0.0, (resample_pos - key_frames[point_index]) / time_range))

            self.resampling_positions[i][...] = getCubicBezierCurvePoint(
                spline_point.position,
                spline_point.position + spline_point.control_point,
                next_spline_point.position - next_spline_point.control_point,
                next_spline_point.position,
                t
            )

            resample_pos = min(total_time, resample_pos + resample_step)


class Spline3D:
    def __init__(self, **spline_data):
        self.name = spline_data.get('name', 'spline')
        self.object_id = spline_data.get('object_id', 0)
        self.transform = TransformObject()
        self.transform.set_pos(spline_data.get('pos', [0, 0, 0]))
        self.transform.set_rotation(spline_data.get('rot', [0, 0, 0]))
        self.transform.set_scale(spline_data.get('scale', [1, 1, 1]))
        self.spline_data = spline_data.get('spline_data')
        self.depth_test = spline_data.get('depth_test', True)
        self.color = Float4(*spline_data.get('color', [1.0, 1.0, 1.0, 1.0]))
        self.width = spline_data.get('width', 1.0)
        self.selected = False
        self.attributes = Attributes()

    def get_object_id(self):
        return self.object_id

    def set_object_id(self, object_id):
        self.object_id = object_id

    def is_selected(self):
        return self.selected

    def set_selected(self, selected):
        self.selected = selected

    def get_attribute(self):
        save_data = self.get_save_data()
        attribute_names = list(save_data.keys())
        attribute_names.sort()

        for attribute_name in attribute_names:
            self.attributes.set_attribute(attribute_name, save_data[attribute_name])
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        if 'spline_data' == attribute_name:
            spline_data = CoreManager.instance().resource_manager.get_spline(attribute_value)
            if spline_data is not None:
                self.spline_data = spline_data
        elif 'color' == attribute_name:
            self.color = Float4(*attribute_value)
        elif attribute_name == 'pos':
            self.transform.set_pos(attribute_value)
        elif attribute_name == 'rot':
            self.transform.set_rotation(attribute_value)
        elif attribute_name == 'scale':
            self.transform.set_scale(attribute_value)
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)

    def get_save_data(self):
        save_data = dict(
            name=self.name,
            spline_data=self.spline_data.name if self.spline_data is not None else '',
            pos=self.transform.pos.tolist(),
            rot=self.transform.rot.tolist(),
            scale=self.transform.scale.tolist(),
            color=self.color.tolist(),
            width=self.width,
            depth_test=self.depth_test
        )
        return save_data

    def get_resampling_position(self, ratio):
        pos = self.spline_data.get_resampling_position(ratio)
        return np.dot(Float4(*pos, 1.0), self.transform.matrix)[:3]

    def update(self, dt):
        self.transform.update_transform(update_inverse_matrix=True)


