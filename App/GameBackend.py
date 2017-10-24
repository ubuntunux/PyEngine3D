import os

import pyglet
from pyglet.gl import *
from pyglet import info

import pygame
from pygame.locals import *

from Common import logger, log_level, COMMAND


class GameBackend:
    enable_font = False
    enable_keyboard = False
    enable_mouse = False

    def __init__(self, core_manager):
        self.running = False
        self.valid = False
        self.core_manager = core_manager

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


class PyGlet(GameBackend):
    enable_font = False
    enable_keyboard = False
    enable_mouse = False

    def __init__(self, core_manager):
        GameBackend.__init__(self, core_manager)

        os.environ['PYGLET_DEBUG_GL'] = '1'
        config = Config(double_buffer=True, )
        # Ubuntu Vsync Off : NVidia X Server Setting -> OpenGL Setting -> Sync To VBlank ( Off )
        self.window = pyglet.window.Window(width=512, height=512, config=config, resizable=True, vsync=False)

        # for debbug
        # self.window.push_handlers(pyglet.window.event.WindowEventLogger())

        # show system info
        # pyglet.info.dump()

        # listen for draw and resize events
        self.window.push_handlers(
            on_draw=self.on_draw,
            on_resize=self.on_resize,
            # on_key_press=self.on_key_press,
            # on_key_release=self.on_key_release
        )

        self.valid = True

    def set_window_title(self, title):
        self.window.set_caption(title)

    def change_resolution(self, width=0, height=0, full_screen=False):
        self.window.set_size(width, height)
        # x, y = window.get_location()
        # selfset_location(x + 20, y + 20)
        self.window.set_fullscreen(full_screen)

    def on_resize(self, width, height):
        return pyglet.event.EVENT_HANDLED

    def on_draw(self):
        pass
        # self.window.clear()
        # self.window.label.draw()
        # self.core_manager.on_draw()

    def flip(self):
        # auto flip by pyglet
        pass

    def run(self):
        self.running = True
        while self.running:
            pyglet.clock.tick()

            for self.window in pyglet.app.windows:
                self.window.switch_to()
                self.window.dispatch_events()
                self.window.dispatch_event('on_draw')
                self.core_manager.update()
                self.window.flip()

    def close(self):
        self.running = False

    def quit(self):
        self.window.close()


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
