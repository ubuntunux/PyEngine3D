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
        self.show = True

        self.pos_x = 0
        self.pos_y = 0
        self.font_size = 10
        self.render_index = 0
        self.render_queues = []

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.quad = self.resource_manager.getMesh("Quad")
        self.font_shader = self.resource_manager.getMaterialInstance("font")

        font_datas = self.resource_manager.getFont('NanumBarunGothic')
        ascii_data = font_datas['ascii']
        self.ascii = FontData(ascii_data)

    def clear_logs(self, screen_width, screen_height):
        self.pos_x = 0
        self.pos_y = screen_height - self.get_font_size()
        self.render_index = 0
        self.render_queues.clear()

    def get_font_size(self):
        return self.ascii.font_size

    def get_font_texture(self):
        return self.ascii.texture

    def toggle(self):
        self.show = not self.show

    def log(self, text, font_size=12):
        if not self.show:
            return
        self.font_size = font_size
        count_ratio = 1.0 / self.ascii.count_horizontal
        render_size = len(self.render_queues)
        text_count = len(text)
        if text_count > render_size - self.render_index:
            self.render_queues.extend([[0,0,0,0], ] * (text_count - (render_size - self.render_index)))

        if self.render_index != 0:
            self.pos_y -= font_size
            self.pos_x = 0

        for c in text:
            if c == '\n':
                self.pos_y -= font_size
                self.pos_x = 0
            elif c == '\t':
                self.pos_x += font_size * 4
            elif c == ' ':
                self.pos_x += font_size
            else:
                index = max(0, ord(c) - self.ascii.range_min)
                texcoord_x = (index % self.ascii.count_horizontal) * count_ratio
                texcoord_y = (self.ascii.count_horizontal - 1 - int(index * count_ratio)) * count_ratio
                self.render_queues[self.render_index] = [self.pos_x, self.pos_y, texcoord_x, texcoord_y]
                self.render_index += 1
                self.pos_x += font_size

    def render_font(self, screen_width, screen_height):
        if self.show and len(self.render_queues) > 0:
            render_queue = np.array(self.render_queues, dtype=np.float32)
            self.quad.bind_vertex_buffer(0, 5, render_queue)
            self.font_shader.use_program()
            self.font_shader.bind_material_instance()
            self.font_shader.bind_uniform_data("texture_font", self.ascii.texture)
            self.font_shader.bind_uniform_data("font_size", self.font_size)
            self.font_shader.bind_uniform_data("screen_size", (screen_width, screen_height))
            self.font_shader.bind_uniform_data("count_horizontal", self.ascii.count_horizontal)
            self.quad.draw_elements_instanced(0, len(self.render_queues))
        self.clear_logs(screen_width, screen_height)