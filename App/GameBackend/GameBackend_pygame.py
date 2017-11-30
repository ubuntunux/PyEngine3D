import os

import pygame
from pygame.locals import *

from Common import logger, log_level, COMMAND
from .GameBackend import GameBackend


class PyGame(GameBackend):
    enable_font = True
    enable_keyboard = True
    enable_mouse = True

    def __init__(self, core_manager):
        GameBackend.__init__(self, core_manager)

        # centered window
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()

        pygame.font.init()
        if not pygame.font.get_init():
            logger.error('Could not render font.')
            return

        self.key.LSHIFT = K_LSHIFT
        self.key.SPACE = K_SPACE
        self.key.Q = K_q
        self.key.W = K_w
        self.key.E = K_e
        self.key.A = K_a
        self.key.S = K_s
        self.key.D = K_d
        self.key.Z = K_z
        self.key.X = K_x
        self.key.C = K_c

        self.key_pressed = dict()
        self.mouse_pressed = dict()

        for key in self.key.__dict__:
            self.key_pressed[self.key.__dict__[key]] = False

        self.valid = True

    def initialize(self):
        pass

    def set_window_title(self, title):
        pygame.display.set_caption(title)

    def change_resolution(self, width=0, height=0, full_screen=False):
        option = OPENGL | DOUBLEBUF | HWPALETTE | HWSURFACE
        if full_screen:
            option |= FULLSCREEN
        return pygame.display.set_mode((width, height), option)

    def on_resize(self, width=0, height=0, full_screen=False):
        return None

    def on_draw(self):
        pass

    def get_keyboard_pressed(self):
        for event in pygame.event.get():
            pass

        return pygame.key.get_pressed()

    def get_mouse_pressed(self):
        return pygame.mouse.get_pressed()

    def flip(self):
        pygame.display.flip()

    def run(self):
        self.running = True
        while self.running:
            self.core_manager.update()

    def close(self):
        self.running = False

    def quit(self):
        pygame.display.quit()
        pygame.quit()

