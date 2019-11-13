import os
import traceback

import numpy as np
from OpenGL.GL import *

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.OpenGLContext import InstanceBuffer
from PyEngine3D.Utilities import *
from . import Line


class DebugLine:
    def __init__(self, pos0, pos1, color=None, width=1.0, life_time=0.0, is_infinite=False, render_once=True):
        self.pos0 = pos0.copy()
        self.pos1 = pos1.copy()
        self.color = color.copy() if color is not None else Float4(1.0, 1.0, 1.0, 1.0)
        self.width = width
        self.life_time = life_time
        self.is_infinite = is_infinite
        self.render_once = render_once
        self.update_count = 0
        self.alive = True

        if 0.0 < life_time:
            self.is_infinite = False
            self.render_once = False
        elif self.is_infinite and self.render_once:
            self.render_once = False

    def update(self, delta_time):
        self.update_count += 1

        if self.is_infinite:
            return

        if self.render_once:
            if 1 < self.update_count:
                self.alive = False
            return

        if self.life_time <= delta_time:
            self.life_time = 0.0
            self.alive = False
        else:
            self.life_time -= delta_time


class DebugLineManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.renderer = None
        self.debug_lines_2d = []
        self.debug_lines_3d = []
        self.debug_line_material = None
        self.debug_line_vertex_buffer = None
        self.debug_line_instance_buffer = None

    def initialize(self, core_manager):
        logger.info("Initialize DebugLineManager")
        self.core_manager = core_manager
        self.renderer = core_manager.renderer

        if not core_manager.is_basic_mode:
            self.debug_line_material = core_manager.resource_manager.get_material_instance("debug_line")
            self.debug_line_vertex_buffer = Line.get_vertex_array_buffer()
            self.debug_line_instance_buffer = InstanceBuffer(name="debug_line_instance_buffer", location_offset=1, element_datas=[FLOAT4_ZERO, FLOAT4_ZERO, FLOAT4_ZERO])

    def update(self, delta):
        def update_func(debug_line_array):
            debug_line_count = len(debug_line_array)
            index = 0
            for i in range(debug_line_count):
                debug_line = debug_line_array[index]
                debug_line.update(delta)
                if not debug_line.alive:
                    debug_line_array.pop(index)
                else:
                    index += 1
        update_func(self.debug_lines_2d)
        update_func(self.debug_lines_3d)

    def clear_debug_lines(self):
        self.debug_lines_2d = []
        self.debug_lines_3d = []

    def draw_debug_line_2d(self, pos0, pos1, color=None, width=1.0, life_time=0.0, is_infinite=False, render_once=True):
        debug_line = DebugLine(Float3(*pos0, -1.0), Float3(*pos1, -1.0), color, width, life_time, is_infinite, render_once)
        self.debug_lines_2d.append(debug_line)

    def draw_debug_line_3d(self, pos0, pos1, color=None, width=1.0, life_time=0.0, is_infinite=False, render_once=True):
        debug_line = DebugLine(pos0, pos1, color, width, life_time, is_infinite, render_once)
        self.debug_lines_3d.append(debug_line)

    def render_debug_line(self):
        if self.core_manager.is_basic_mode:
            glPushMatrix()
            glLoadIdentity()
            for debug_line in self.debug_lines_2d:
                glLineWidth(debug_line.width)
                glColor3f(*debug_line.color)
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
            def draw_debug_line(debug_lines):
                for debug_line in debug_lines:
                    glLineWidth(debug_line.width)
                    self.debug_line_material.bind_uniform_data("position0", debug_line.pos0)
                    self.debug_line_material.bind_uniform_data("position1", debug_line.pos1)
                    self.debug_line_material.bind_uniform_data("color", debug_line.color)
                    self.debug_line_vertex_buffer.draw_elements()

            glDisable(GL_DEPTH_TEST)
            self.debug_line_material.use_program()
            self.debug_line_material.bind_material_instance()
            self.debug_line_material.bind_uniform_data("is_debug_line_2d", True)
            draw_debug_line(self.debug_lines_2d)

            glEnable(GL_DEPTH_TEST)
            self.debug_line_material.bind_uniform_data("is_debug_line_2d", False)
            draw_debug_line(self.debug_lines_3d)

