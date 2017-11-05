import math

from App import CoreManager
from Common import logger, log_level, COMMAND
from Utilities import *


class FontData:
    def __init__(self, font_data):
        self.range_min = font_data['range_min']
        self.range_max = font_data['range_max']
        self.text_count = font_data['text_count']
        self.count_horizontal = int(math.ceil(math.sqrt(float(self.text_count))))
        self.font_size = font_data['font_size']
        self.texture = font_data['texture']


class FontManager(Singleton):
    def __init__(self):
        self.name = 'FontManager'
        self.core_manager = None
        self.resource_manager = None
        self.font_shader = None
        self.quad = None
        self.ascii = None
        self.render_queues = []

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.quad = self.resource_manager.getMesh("Quad")
        self.font_shader = self.resource_manager.getMaterialInstance("font")

        font_datas = self.resource_manager.getFont('NanumBarunGothic')
        ascii_data = font_datas['ascii']
        self.ascii = FontData(ascii_data)

    def clear(self):
        self.render_queues = []

    def get_font_texture(self):
        return self.ascii.texture

    def log(self, text, x, y):
        pos_x = x
        pos_y = y
        for c in text:
            if c == '\n':
                pos_y -= 1
            elif c == '\t':
                pos_x += 4
            elif c == ' ':
                pos_x += 1
            else:
                index = max(0, ord(c) - self.ascii.range_min)
                texcoord_x = (index % self.ascii.count_horizontal) / self.ascii.count_horizontal
                texcoord_y = int(index / self.ascii.count_horizontal) / self.ascii.count_horizontal
                self.render_queues.append((pos_x, pos_y, texcoord_x, texcoord_y))
                pos_x += 1

    def render_font(self, screen_width, screen_height):
        self.quad.bind_vertex_buffer()
        self.font_shader.use_program()
        self.font_shader.bind_material_instance()
        self.font_shader.bind_uniform_data("texture_font", self.ascii.texture)
        self.font_shader.bind_uniform_data("font_size", self.ascii.font_size)
        self.font_shader.bind_uniform_data("screen_size", (screen_width, screen_height))
        self.font_shader.bind_uniform_data("count_horizontal", self.ascii.count_horizontal)
        for render_queue in self.render_queues:
            self.font_shader.bind_uniform_data("font_offset", render_queue)
            self.quad.draw_elements()





