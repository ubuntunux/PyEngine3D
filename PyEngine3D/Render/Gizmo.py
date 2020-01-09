from math import *
import numpy as np

from PyEngine3D.Common import logger
from PyEngine3D.App.CoreManager import CoreManager
from PyEngine3D.Utilities import *
from . import StaticActor


def count_generator(num):
    while True:
        yield num
        num += 1


class AxisGizmo(StaticActor):
    counter = count_generator(0)
    ID_NONE = 0
    ID_START = 1
    ID_POSITION_Z = ID_START + next(counter)
    ID_ROTATION_YAW = ID_START + next(counter)
    ID_POSITION_XZ = ID_START + next(counter)
    ID_ROTATION_PITCH = ID_START + next(counter)
    ID_POSITION_YZ = ID_START + next(counter)
    ID_ROTATION_ROLL = ID_START + next(counter)
    ID_POSITION_XY = ID_START + next(counter)
    ID_POSITION_Y = ID_START + next(counter)
    ID_POSITION_X = ID_START + next(counter)
    ID_SCALE_Z = ID_START + next(counter)
    ID_SCALE_X = ID_START + next(counter)
    ID_SCALE_Y = ID_START + next(counter)
    ID_COUNT = ID_START + next(counter)

    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)

        axis_gizmo_geometry_count = self.get_geometry_count()
        assert (axis_gizmo_geometry_count == (AxisGizmo.ID_COUNT - AxisGizmo.ID_START))

        self.axis_gizmo_colors = [Float4(1.0, 1.0, 1.0, 1.0) for i in range(AxisGizmo.ID_COUNT)]
        self.axis_gizmo_colors[AxisGizmo.ID_POSITION_X][0:3] = Float3(1.0, 0.0, 0.0)
        self.axis_gizmo_colors[AxisGizmo.ID_POSITION_Y][0:3] = Float3(0.0, 1.0, 0.0)
        self.axis_gizmo_colors[AxisGizmo.ID_POSITION_Z][0:3] = Float3(0.0, 0.0, 1.0)
        self.axis_gizmo_colors[AxisGizmo.ID_POSITION_XY][0:3] = Float3(1.0, 1.0, 0.0)
        self.axis_gizmo_colors[AxisGizmo.ID_POSITION_XZ][0:3] = Float3(1.0, 0.0, 1.0)
        self.axis_gizmo_colors[AxisGizmo.ID_POSITION_YZ][0:3] = Float3(0.0, 1.0, 1.0)
        self.axis_gizmo_colors[AxisGizmo.ID_ROTATION_PITCH][0:3] = Float3(1.0, 0.0, 0.0)
        self.axis_gizmo_colors[AxisGizmo.ID_ROTATION_YAW][0:3] = Float3(0.0, 1.0, 0.0)
        self.axis_gizmo_colors[AxisGizmo.ID_ROTATION_ROLL][0:3] = Float3(0.0, 0.0, 1.0)
        self.axis_gizmo_colors[AxisGizmo.ID_SCALE_X][0:3] = Float3(1.0, 0.0, 0.0)
        self.axis_gizmo_colors[AxisGizmo.ID_SCALE_Y][0:3] = Float3(0.0, 1.0, 0.0)
        self.axis_gizmo_colors[AxisGizmo.ID_SCALE_Z][0:3] = Float3(0.0, 0.0, 1.0)

    def get_object_color(self, index):
        return self.axis_gizmo_colors[self.get_object_id(index)]

    def get_object_id(self, index):
        return AxisGizmo.ID_START + index
