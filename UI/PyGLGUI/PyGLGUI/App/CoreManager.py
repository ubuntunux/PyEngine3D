import gc
import time

from .GameBackend import PyGlet, PyGame, Keyboard, Event
from ..Common import logger
from ..Utilities import Singleton


class CoreManager(Singleton):
    def __init__(self):
        self.valid = True

        self.need_to_gc_collect = False

        # timer
        self.fps = 0.0
        self.vsync = False
        self.min_delta = 1.0 / 60.0  # 60fps
        self.delta = 0.0
        self.update_time = 0.0
        self.current_time = 0.0

        # managers
        self.game_backend = None
        self.resource_manager = None
        self.renderer = None
        self.rendertarget_manager = None
        self.font_manager = None
        self.config = None

        self.last_game_backend = PyGlet.__name__
        self.game_backend_list = [PyGlet.__name__, PyGame.__name__]

        self.commands = []

    def gc_collect(self):
        self.need_to_gc_collect = True

    def initialize(self):
        from .. import ResourceManager
        from .. import RenderTargetManager, FontManager
        from .Renderer import Renderer

        self.resource_manager = ResourceManager.instance()
        self.rendertarget_manager = RenderTargetManager.instance()
        self.font_manager = FontManager.instance()
        self.renderer = Renderer.instance()

        # do First than other manager initalize. Because have to been opengl init from pygame.display.set_mode
        width, height = 1280, 720
        full_screen = False

        self.last_game_backend = PyGame.__name__

        if self.last_game_backend == PyGame.__name__:
            self.game_backend = PyGame(self)
        else:
            self.game_backend = PyGlet(self)
            self.last_game_backend = PyGlet.__name__
        self.game_backend.change_resolution(width, height, full_screen, resize_scene=False)

        if not self.game_backend.valid:
            self.error('game_backend initializing failed')

        # initalize managers
        self.resource_manager.initialize()
        self.rendertarget_manager.initialize(self)
        self.font_manager.initialize(self)
        self.renderer.initialize(self)
        self.renderer.resizeScene(width, height)

        return True

    def set_window_title(self, title):
        self.game_backend.set_window_title(self.last_game_backend + " - " + title)

    def run(self):
        self.game_backend.run()
        self.exit()

    def exit(self):
        self.renderer.close()
        self.resource_manager.close()
        self.renderer.destroyScreen()

        self.game_backend.quit()

    def error(self, msg):
        logger.error(msg)
        self.close()

    def close(self):
        self.game_backend.close()

    def change_game_backend(self, game_backend):
        self.last_game_backend = self.game_backend_list[game_backend]
        logger.info("The game backend was chaned to %s. It will be applied at the next run." % self.last_game_backend)

    def get_mouse_pos(self):
        return self.game_backend.mouse_pos

    def update_event(self, event_type, event_value=None):
        if Event.QUIT == event_type:
            self.close()
        elif Event.VIDEORESIZE == event_type:
            pass
        elif Event.KEYDOWN == event_type:
            key_pressed = self.game_backend.get_keyboard_pressed()
            subkey_down = key_pressed[Keyboard.LCTRL] or key_pressed[Keyboard.LSHIFT] or key_pressed[Keyboard.LALT]
            if Keyboard.ESCAPE == event_value:
                if self.game_backend.full_screen:
                    self.game_backend.change_resolution(0, 0, False)
                else:
                    self.close()

    def update(self):
        current_time = time.perf_counter()
        delta = current_time - self.current_time

        if self.vsync and delta < self.min_delta or delta == 0.0:
            return

        # set timer
        self.current_time = current_time
        self.delta = delta
        self.fps = 1.0 / delta

        self.update_time = delta * 1000.0  # millisecond

        self.resource_manager.update()

        self.renderer.renderScene()

        # debug info
        self.font_manager.log("DEBUG TEST")

        if self.need_to_gc_collect:
            self.need_to_gc_collect = False
            gc.collect()

