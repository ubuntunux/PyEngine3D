import math

import numpy as np

from PyEngine3D.App import CoreManager
from PyEngine3D.OpenGLContext import InstanceBuffer
from PyEngine3D.Common import logger, log_level, COMMAND
from PyEngine3D.Utilities import *
from .Mesh import ScreenQuad
from .RenderOptions import RenderOption


class TextRenderData:
    def __init__(self):
        self.text = ""
        self.column = 0
        self.row = 0
        self.font_size = 10
        self.width = 0
        self.height = 0
        self.render_count = 0
        self.render_queue = None

    def set_text(self, text, font_data, initial_column=0, initial_row=0, font_size=10):
        if self.text == text:
            return

        ratio = 1.0 / font_data.count_of_side
        text_count = len(text)
        render_queue = np.array([[0, 0, 0, 0], ] * text_count, dtype=np.float32)
        render_index = 0
        max_column = initial_column
        column = initial_column
        row = initial_row

        for c in text:
            if c == '\n':
                column = initial_column
                row += 1
            elif c == '\t':
                column += 1
            elif c == ' ':
                column += 1
            else:
                index = max(0, ord(c) - font_data.range_min)
                texcoord_x = (index % font_data.count_of_side) * ratio
                texcoord_y = (font_data.count_of_side - 1 - int(index * ratio)) * ratio
                render_queue[render_index] = [column, row, texcoord_x, texcoord_y]
                render_index += 1
                column += 1
            max_column = max(max_column, column)

        self.text = text
        self.column = max_column - initial_column
        self.row = row - initial_row
        self.font_size = font_size
        self.width = self.column * font_size
        self.height = self.row * font_size
        self.render_queue = render_queue
        self.render_count = render_index


class FontData:
    def __init__(self, font_data):
        self.range_min = font_data['range_min']
        self.range_max = font_data['range_max']
        self.text_count = font_data['text_count']
        self.count_of_side = font_data['count_of_side']
        self.font_size = font_data['font_size']
        self.texture = font_data['texture']


class FontManager(Singleton):
    def __init__(self):
        self.name = 'FontManager'
        self.core_manager = None
        self.resource_manager = None
        self.font_shader = None
        self.quad = None
        self.instance_buffer = None
        self.ascii = None
        self.show = True

        self.column = 0
        self.row = 0
        self.font_size = 12
        self.render_index = 0
        self.render_queue = []

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.font_shader = self.resource_manager.get_material_instance("font")

        font_datas = self.resource_manager.get_default_font()
        ascii_data = font_datas['ascii']
        self.ascii = FontData(ascii_data)

        self.quad = ScreenQuad.get_vertex_array_buffer()

        # layout(location=1) vec4 font_offset;
        self.instance_buffer = InstanceBuffer(name="font_offset",
                                              location_offset=1,
                                              element_datas=[FLOAT4_ZERO, ])

    def clear_logs(self):
        self.column = 0
        self.row = 0
        self.render_index = 0
        self.render_queue.clear()

    def get_default_font_data(self):
        return self.ascii

    def get_font_size(self):
        return self.ascii.font_size

    def get_font_texture(self):
        return self.ascii.texture

    def toggle(self):
        self.show = not self.show

    def log(self, text):
        if not self.show or not RenderOption.RENDER_FONT:
            return

        ratio = 1.0 / self.ascii.count_of_side
        render_size = len(self.render_queue)
        text_count = len(text)
        if text_count > render_size - self.render_index:
            self.render_queue.extend([[0, 0, 0, 0], ] * (text_count - (render_size - self.render_index)))

        if self.render_index != 0:
            self.column = 0
            self.row += 1

        for c in text:
            if c == '\n':
                self.column = 0
                self.row += 1
            elif c == '\t':
                self.column += 4
            elif c == ' ':
                self.column += 1
            else:
                index = max(0, ord(c) - self.ascii.range_min)
                texcoord_x = (index % self.ascii.count_of_side) * ratio
                texcoord_y = (self.ascii.count_of_side - 1 - int(index * ratio)) * ratio
                self.render_queue[self.render_index] = [self.column, self.row, texcoord_x, texcoord_y]
                self.render_index += 1
                self.column += 1

    def render_log(self, canvas_width, canvas_height):
        if RenderOption.RENDER_FONT and self.show and 0 < len(self.render_queue):
            render_queue = np.array(self.render_queue, dtype=np.float32)
            self.render_font(0.0, canvas_height - self.font_size, canvas_width, canvas_height, self.font_size, render_queue, self.render_index)
            self.clear_logs()

    def render_font(self, offset_x, offset_y, canvas_width, canvas_height, font_size, render_queue, text_render_count):
        self.font_shader.use_program()
        self.font_shader.bind_material_instance()
        self.font_shader.bind_uniform_data("texture_font", self.ascii.texture)
        self.font_shader.bind_uniform_data("font_size", font_size)
        self.font_shader.bind_uniform_data("offset", (offset_x, offset_y))
        self.font_shader.bind_uniform_data("inv_canvas_size", (1.0 / canvas_width, 1.0 / canvas_height))
        self.font_shader.bind_uniform_data("count_of_side", self.ascii.count_of_side)
        self.quad.draw_elements_instanced(text_render_count, self.instance_buffer, [render_queue, ])
