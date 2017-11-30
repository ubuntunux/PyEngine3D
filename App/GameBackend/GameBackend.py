import os
from Common import logger, log_level, COMMAND


class KEY:
    pass


class GameBackend:
    enable_font = False
    enable_keyboard = False
    enable_mouse = False

    def __init__(self, core_manager):
        self.running = False
        self.valid = False
        self.core_manager = core_manager
        self.key = KEY()

    def set_window_title(self, title):
        raise BaseException('You muse implement.')

    def change_resolution(self, width=0, height=0, full_screen=False):
        raise BaseException('You muse implement.')

    def run(self):
        raise BaseException('You muse implement.')

    def on_resize(self, width, height):
        raise BaseException('You muse implement.')

    def on_draw(self, *args):
        raise BaseException('You muse implement.')

    def flip(self):
        raise BaseException('You muse implement.')

    def quit(self):
        raise BaseException('You muse implement.')
