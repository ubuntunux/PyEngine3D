import numpy as np

from PyEngine3D.Utilities import *
from .RenderOptions import RenderOption


class TextRenderData:
    def __init__(self):
        self._text = ""
        self.column = 0
        self.row = 0
        self.font_size = 10
        self.width = 0.0
        self.height = 0.0
        self.initial_column = 0
        self.initial_row = 0
        self.font_data = None
        self.render_count = 0
        self.render_queue = np.zeros(1, (np.float32, 4))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text

        ratio = 1.0 / self.font_data.count_of_side
        text_count = len(text)

        if len(self.render_queue) < text_count:
            self.render_queue.resize((text_count, 4), refcheck=False)

        render_index = 0
        max_column = self.initial_column
        column = self.initial_column
        row = self.initial_row

        for c in text:
            if c == '\n':
                column = self.initial_column
                row += 1
            elif c == '\t':
                column += 1
            elif c == ' ':
                column += 1
            else:
                index = max(0, ord(c) - self.font_data.range_min)
                texcoord_x = (index % self.font_data.count_of_side) * ratio
                texcoord_y = (self.font_data.count_of_side - 1 - int(index * ratio)) * ratio
                self.render_queue[render_index][...] = [column, row, texcoord_x, texcoord_y]
                render_index += 1
                column += 1
            max_column = max(max_column, column)
        row += 1

        self.column = max_column - self.initial_column
        self.row = row - self.initial_row
        self.width = self.column * self.font_size
        self.height = self.row * self.font_size
        self.render_count = render_index

    def set_text(self, text, font_data, initial_column=0, initial_row=0, font_size=10, skip_check=False):
        if not skip_check and text == self.text:
            return False

        self.font_data = font_data
        self.font_size = font_size
        self.initial_column = initial_column
        self.initial_row = initial_row

        self.text = text
        return True


class FontData:
    def __init__(self, unicode_block_name, font_data):
        self.unicode_block_name = unicode_block_name
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
        self.ascii = None
        self.show = True

        self.logs = []
        self.text_render_data = None

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.ascii = self.resource_manager.get_default_font_data()
        self.text_render_data = TextRenderData()

    def clear_logs(self):
        self.logs = []
        self.text_render_data.set_text("", self.ascii, font_size=12)

    def toggle(self):
        self.show = not self.show

    def log(self, text):
        if not self.show or not RenderOption.RENDER_FONT:
            return

        self.logs.append(text)

    def render_log(self, canvas_width, canvas_height):
        if RenderOption.RENDER_FONT and self.show and 0 < len(self.logs):
            text = "\n".join(self.logs)
            self.logs = []
            self.text_render_data.set_text(text, self.ascii, font_size=12, skip_check=True)
            self.core_manager.renderer.render_text(self.text_render_data, 0.0, canvas_height - self.text_render_data.font_size, canvas_width, canvas_height)
