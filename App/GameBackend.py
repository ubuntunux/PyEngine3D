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


class PyGlet(pyglet.window.Window, GameBackend):
    enable_font = True
    enable_keyboard = True
    enable_mouse = True

    def __init__(self, core_manager):
        GameBackend.__init__(self, core_manager)

        os.environ['PYGLET_DEBUG_GL'] = '1'
        config = Config(double_buffer=True, )
        # Ubuntu Vsync Off : NVidia X Server Setting -> OpenGL Setting -> Sync To VBlank ( Off )
        pyglet.window.Window.__init__(self, width=512, height=512, config=config, resizable=True, vsync=False)

        # for debbug
        # self.push_handlers(pyglet.window.event.WindowEventLogger())

        # show system info
        # pyglet.info.dump()

        self.valid = True

    def set_window_title(self, title):
        self.set_caption(title)

    def change_resolution(self, width=0, height=0, full_screen=False):
        self.set_size(width, height)
        # x, y = window.get_location()
        # selfset_location(x + 20, y + 20)
        self.set_fullscreen(full_screen)

    def on_resize(self, width, height):
        return pyglet.event.EVENT_HANDLED

    def on_draw(self):
        pass
        #self.clear()
        #self.label.draw()
        #self.core_manager.on_draw()

    def flip(self):
        pass

    def run(self):
        self.running = True
        pyglet.clock.schedule(self.core_manager.update)
        # main loop
        pyglet.app.run()

    def close(self):
        self.running = False
        pyglet.clock.unschedule(self.core_manager.update)

    def quit(self):
        pass


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
