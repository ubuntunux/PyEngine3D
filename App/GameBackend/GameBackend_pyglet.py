import os

import pyglet
from pyglet.gl import *
from pyglet import info
from pyglet.window import key
from pyglet.window import mouse

from Common import logger, log_level, COMMAND
from .GameBackend import GameBackend


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
            on_key_press=self.on_key_press,
            on_key_release=self.on_key_release,
            on_mouse_press=self.on_mouse_press,
            on_mouse_release=self.on_mouse_release
        )

        self.key.LSHIFT = pyglet.window.key.LSHIFT
        self.key.SPACE = pyglet.window.key.SPACE
        self.key.Q = pyglet.window.key.Q
        self.key.W = pyglet.window.key.W
        self.key.E = pyglet.window.key.E
        self.key.A = pyglet.window.key.A
        self.key.S = pyglet.window.key.S
        self.key.D = pyglet.window.key.D
        self.key.Z = pyglet.window.key.Z
        self.key.X = pyglet.window.key.X
        self.key.C = pyglet.window.key.C

        self.key_pressed = dict()
        self.mouse_pressed = dict()

        for key in self.key.__dict__:
            print(key)
            self.key_pressed[self.key.__dict__[key]] = False

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

    def on_mouse_press(self, x, y, button, modifiers):
        print(3, x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        print(4, x, y, button, modifiers)

    def on_key_press(self, symbol, modifiers):
        self.key_pressed[symbol] = True

    def on_key_release(self, symbol, modifiers):
        self.key_pressed[symbol] = False

    def get_keyboard_pressed(self):
        return self.key_pressed

    def get_mouse_pressed(self):
        return False, False, False

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

    def get_keyboard_pressed(self):
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
