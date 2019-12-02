import os
import traceback

import numpy as np
from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.OpenGLContext import InstanceBuffer
from PyEngine3D.Utilities import *
from . import Line, ScreenQuad


class DebugLine:
    def __init__(self, pos0, pos1, color=None, width=1.0):
        self.pos0 = pos0.copy()
        self.pos1 = pos1.copy()
        self.color = color.copy() if color is not None else Float4(1.0, 1.0, 1.0, 1.0)
        self.width = width
        self.alive = True

    def update(self, delta_time):
        pass


class DebugLineManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.renderer = None
        self.debug_lines_2d = []
        self.debug_lines_3d = []
        self.debug_line_material = None
        self.debug_line_vertex_buffer = None
        self.debug_line_instance_buffer = None
        self.debug_line_instance_data = None
        self.debug_line_instance_element_data = [FLOAT4_ZERO, FLOAT4_ZERO, FLOAT4_ZERO, FLOAT4_ZERO]

    def initialize(self, core_manager):
        logger.info("Initialize DebugLineManager")
        self.core_manager = core_manager
        self.renderer = core_manager.renderer

        if not core_manager.is_basic_mode:
            self.debug_line_material = core_manager.resource_manager.get_material_instance("debug_line")
            self.debug_line_vertex_buffer = ScreenQuad.get_vertex_array_buffer()
            self.debug_line_instance_buffer = InstanceBuffer(name="debug_line_instance_buffer", location_offset=1, element_datas=self.debug_line_instance_element_data)
            self.resize_debug_line_instance_data(10)

    def resize_debug_line_instance_data(self, count):
        if self.debug_line_instance_data is None or (len(self.debug_line_instance_data) / len(self.debug_line_instance_element_data)) < count:
            element = [[0.0, 0.0, 0.0, 0.0]] * count
            self.debug_line_instance_data = np.array([element, element, element, element], dtype=np.float32)

    def clear_debug_lines(self):
        self.debug_lines_2d = []
        self.debug_lines_3d = []

    def draw_debug_line_2d(self, pos0, pos1, color=None, width=1.0):
        debug_line = DebugLine(Float3(*pos0, -1.0), Float3(*pos1, -1.0), color, width)
        self.debug_lines_2d.append(debug_line)

    def draw_debug_line_3d(self, pos0, pos1, color=None, width=1.0):
        debug_line = DebugLine(pos0, pos1, color, width)
        self.debug_lines_3d.append(debug_line)

    def bind_render_spline_program(self):
        self.debug_line_material.use_program()
        self.debug_line_material.bind_material_instance()
        self.debug_line_material.bind_uniform_data("is_debug_line_2d", False)

    def render_spline(self, spline, custom_color=None, add_width=0.0):
        spline_color = custom_color if custom_color is not None else spline.color
        spline_width = spline.width + add_width
        resampling_count = len(spline.spline_data.resampling_positions)
        if 1 < resampling_count:
            debug_lines = []
            for i in range(resampling_count - 1):
                debug_line = DebugLine(
                    spline.spline_data.resampling_positions[i],
                    spline.spline_data.resampling_positions[i + 1],
                    color=spline_color,
                    width=spline_width
                )
                debug_lines.append(debug_line)

            if spline.depth_test:
                glEnable(GL_DEPTH_TEST)
            else:
                glDisable(GL_DEPTH_TEST)
            self.debug_line_material.bind_uniform_data("transform", spline.transform.matrix)
            self.render_lines(debug_lines)

    def render_lines(self, debug_lines):
        line_count = len(debug_lines)
        if 0 < line_count:
            self.resize_debug_line_instance_data(line_count)

            for i, debug_line in enumerate(debug_lines):
                self.debug_line_instance_data[0][i][0:3] = debug_line.pos0
                self.debug_line_instance_data[1][i][0:3] = debug_line.pos1
                self.debug_line_instance_data[2][i][0:4] = debug_line.color
                self.debug_line_instance_data[3][i][0] = debug_line.width

            self.debug_line_vertex_buffer.draw_elements_instanced(
                line_count,
                instance_buffer=self.debug_line_instance_buffer,
                instance_datas=self.debug_line_instance_data
            )

    def render_debug_lines(self):
        if self.core_manager.is_basic_mode:
            glPushMatrix()
            glLoadIdentity()
            for debug_line in self.debug_lines_2d:
                glLineWidth(debug_line.width)
                glColor4f(*debug_line.color)
                glBegin(GL_LINES)
                glVertex3f(*debug_line.pos0)
                glVertex3f(*debug_line.pos1)
                glEnd()
            glPopMatrix()

            glPushMatrix()
            self.renderer.perspective_view(look_at=True)

            for debug_line in self.debug_lines_3d:
                glLineWidth(debug_line.width)
                glColor4f(*debug_line.color)
                glBegin(GL_LINES)
                glVertex3f(*debug_line.pos0)
                glVertex3f(*debug_line.pos1)
                glEnd()
            glPopMatrix()
        else:
            glDisable(GL_DEPTH_TEST)
            self.debug_line_material.use_program()
            self.debug_line_material.bind_material_instance()
            self.debug_line_material.bind_uniform_data("is_debug_line_2d", True)
            self.render_lines(self.debug_lines_2d)

            self.debug_line_material.bind_uniform_data("is_debug_line_2d", False)
            self.debug_line_material.bind_uniform_data("transform", MATRIX4_IDENTITY)
            self.render_lines(self.debug_lines_3d)
