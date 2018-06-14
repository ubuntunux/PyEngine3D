import os

import numpy as np

import pyglet
from pyglet.gl import *
from pyglet import info
from pyglet.window import key
from pyglet.window import mouse

from Common import logger, log_level, COMMAND
from .GameBackend import GameBackend, Keyboard, Event


class PyGlet(GameBackend):
    enable_font = False
    enable_keyboard = False
    enable_mouse = False

    def __init__(self, core_manager):
        GameBackend.__init__(self, core_manager)

        # os.environ['PYGLET_DEBUG_GL'] = '1'
        config = Config(double_buffer=True, )

        # Ubuntu Vsync Off : NVidia X Server Setting -> OpenGL Setting -> Sync To VBlank ( Off )
        self.window = pyglet.window.Window(width=1024, height=768, config=config, resizable=True, vsync=False)

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
            on_mouse_release=self.on_mouse_release,
            on_mouse_motion=self.on_mouse_motion,
            on_mouse_drag=self.on_mouse_drag,
            on_mouse_enter=self.on_mouse_enter,
            on_mouse_leave=self.on_mouse_leave,
        )

        # ASCII commands
        Keyboard.BACKSPACE = pyglet.window.key.BACKSPACE
        Keyboard.TAB = pyglet.window.key.TAB
        Keyboard.LINEFEED = pyglet.window.key.LINEFEED
        Keyboard.CLEAR = pyglet.window.key.CLEAR
        Keyboard.RETURN = pyglet.window.key.RETURN
        Keyboard.ENTER = pyglet.window.key.ENTER
        Keyboard.PAUSE = pyglet.window.key.PAUSE
        Keyboard.SCROLLLOCK = pyglet.window.key.SCROLLLOCK
        Keyboard.SYSREQ = pyglet.window.key.SYSREQ
        Keyboard.ESCAPE = pyglet.window.key.ESCAPE
        Keyboard.SPACE = pyglet.window.key.SPACE

        # Cursor control and motion
        Keyboard.HOME = pyglet.window.key.HOME
        Keyboard.LEFT = pyglet.window.key.LEFT
        Keyboard.UP = pyglet.window.key.UP
        Keyboard.RIGHT = pyglet.window.key.RIGHT
        Keyboard.DOWN = pyglet.window.key.DOWN
        Keyboard.PAGEUP = pyglet.window.key.PAGEUP
        Keyboard.PAGEDOWN = pyglet.window.key.PAGEDOWN
        Keyboard.END = pyglet.window.key.END
        Keyboard.BEGIN = pyglet.window.key.BEGIN

        # Misc functions
        Keyboard.DELETE = pyglet.window.key.DELETE
        Keyboard.SELECT = pyglet.window.key.SELECT
        Keyboard.PRINT = pyglet.window.key.PRINT
        Keyboard.EXECUTE = pyglet.window.key.EXECUTE
        Keyboard.INSERT = pyglet.window.key.INSERT
        Keyboard.UNDO = pyglet.window.key.UNDO
        Keyboard.REDO = pyglet.window.key.REDO
        Keyboard.MENU = pyglet.window.key.MENU
        Keyboard.FIND = pyglet.window.key.FIND
        Keyboard.CANCEL = pyglet.window.key.CANCEL
        Keyboard.HELP = pyglet.window.key.HELP
        Keyboard.BREAK = pyglet.window.key.BREAK
        Keyboard.MODESWITCH = pyglet.window.key.MODESWITCH
        Keyboard.SCRIPTSWITCH = pyglet.window.key.SCRIPTSWITCH
        Keyboard.FUNCTION = pyglet.window.key.FUNCTION

        # Number pad
        Keyboard.NUMLOCK = pyglet.window.key.NUMLOCK
        Keyboard.NUM_SPACE = pyglet.window.key.NUM_SPACE
        Keyboard.NUM_TAB = pyglet.window.key.NUM_TAB
        Keyboard.NUM_ENTER = pyglet.window.key.NUM_ENTER
        Keyboard.NUM_F1 = pyglet.window.key.NUM_F1
        Keyboard.NUM_F2 = pyglet.window.key.NUM_F2
        Keyboard.NUM_F3 = pyglet.window.key.NUM_F3
        Keyboard.NUM_F4 = pyglet.window.key.NUM_F4
        Keyboard.NUM_HOME = pyglet.window.key.NUM_HOME
        Keyboard.NUM_LEFT = pyglet.window.key.NUM_LEFT
        Keyboard.NUM_UP = pyglet.window.key.NUM_UP
        Keyboard.NUM_RIGHT = pyglet.window.key.NUM_RIGHT
        Keyboard.NUM_DOWN = pyglet.window.key.NUM_DOWN
        Keyboard.NUM_PRIOR = pyglet.window.key.NUM_PRIOR
        Keyboard.NUM_PAGE_UP = pyglet.window.key.NUM_PAGE_UP
        Keyboard.NUM_NEXT = pyglet.window.key.NUM_NEXT
        Keyboard.NUM_PAGE_DOWN = pyglet.window.key.NUM_PAGE_DOWN
        Keyboard.NUM_END = pyglet.window.key.NUM_END
        Keyboard.NUM_BEGIN = pyglet.window.key.NUM_BEGIN
        Keyboard.NUM_INSERT = pyglet.window.key.NUM_INSERT
        Keyboard.NUM_DELETE = pyglet.window.key.NUM_DELETE
        Keyboard.NUM_EQUAL = pyglet.window.key.NUM_EQUAL
        Keyboard.NUM_MULTIPLY = pyglet.window.key.NUM_MULTIPLY
        Keyboard.NUM_ADD = pyglet.window.key.NUM_ADD
        Keyboard.NUM_SEPARATOR = pyglet.window.key.NUM_SEPARATOR
        Keyboard.NUM_SUBTRACT = pyglet.window.key.NUM_SUBTRACT
        Keyboard.NUM_DECIMAL = pyglet.window.key.NUM_DECIMAL
        Keyboard.NUM_DIVIDE = pyglet.window.key.NUM_DIVIDE

        Keyboard.NUM_0 = pyglet.window.key.NUM_0
        Keyboard.NUM_1 = pyglet.window.key.NUM_1
        Keyboard.NUM_2 = pyglet.window.key.NUM_2
        Keyboard.NUM_3 = pyglet.window.key.NUM_3
        Keyboard.NUM_4 = pyglet.window.key.NUM_4
        Keyboard.NUM_5 = pyglet.window.key.NUM_5
        Keyboard.NUM_6 = pyglet.window.key.NUM_6
        Keyboard.NUM_7 = pyglet.window.key.NUM_7
        Keyboard.NUM_8 = pyglet.window.key.NUM_8
        Keyboard.NUM_9 = pyglet.window.key.NUM_9

        # Function keys
        Keyboard.F1 = pyglet.window.key.F1
        Keyboard.F2 = pyglet.window.key.F2
        Keyboard.F3 = pyglet.window.key.F3
        Keyboard.F4 = pyglet.window.key.F4
        Keyboard.F5 = pyglet.window.key.F5
        Keyboard.F6 = pyglet.window.key.F6
        Keyboard.F7 = pyglet.window.key.F7
        Keyboard.F8 = pyglet.window.key.F8
        Keyboard.F9 = pyglet.window.key.F9
        Keyboard.F10 = pyglet.window.key.F10
        Keyboard.F11 = pyglet.window.key.F11
        Keyboard.F12 = pyglet.window.key.F12
        Keyboard.F13 = pyglet.window.key.F13
        Keyboard.F14 = pyglet.window.key.F14
        Keyboard.F15 = pyglet.window.key.F15
        Keyboard.F16 = pyglet.window.key.F16
        Keyboard.F17 = pyglet.window.key.F17
        Keyboard.F18 = pyglet.window.key.F18
        Keyboard.F19 = pyglet.window.key.F19
        Keyboard.F20 = pyglet.window.key.F20

        # Modifiers
        Keyboard.LSHIFT = pyglet.window.key.LSHIFT
        Keyboard.RSHIFT = pyglet.window.key.RSHIFT
        Keyboard.LCTRL = pyglet.window.key.LCTRL
        Keyboard.RCTRL = pyglet.window.key.RCTRL
        Keyboard.CAPSLOCK = pyglet.window.key.CAPSLOCK
        Keyboard.LMETA = pyglet.window.key.LMETA
        Keyboard.RMETA = pyglet.window.key.RMETA
        Keyboard.LALT = pyglet.window.key.LALT
        Keyboard.RALT = pyglet.window.key.RALT
        Keyboard.LWINDOWS = pyglet.window.key.LWINDOWS
        Keyboard.RWINDOWS = pyglet.window.key.RWINDOWS
        Keyboard.LCOMMAND = pyglet.window.key.LCOMMAND
        Keyboard.RCOMMAND = pyglet.window.key.RCOMMAND
        Keyboard.LOPTION = pyglet.window.key.LOPTION
        Keyboard.ROPTION = pyglet.window.key.ROPTION

        # Latin-1
        Keyboard.SPACE = pyglet.window.key.SPACE
        Keyboard.EXCLAMATION = pyglet.window.key.EXCLAMATION
        Keyboard.DOUBLEQUOTE = pyglet.window.key.DOUBLEQUOTE
        Keyboard.HASH = pyglet.window.key.HASH
        Keyboard.POUND = pyglet.window.key.POUND
        Keyboard.DOLLAR = pyglet.window.key.DOLLAR
        Keyboard.PERCENT = pyglet.window.key.PERCENT
        Keyboard.AMPERSAND = pyglet.window.key.AMPERSAND
        Keyboard.APOSTROPHE = pyglet.window.key.APOSTROPHE
        Keyboard.PARENLEFT = pyglet.window.key.PARENLEFT
        Keyboard.PARENRIGHT = pyglet.window.key.PARENRIGHT
        Keyboard.ASTERISK = pyglet.window.key.ASTERISK
        Keyboard.PLUS = pyglet.window.key.PLUS
        Keyboard.COMMA = pyglet.window.key.COMMA
        Keyboard.MINUS = pyglet.window.key.MINUS
        Keyboard.PERIOD = pyglet.window.key.PERIOD
        Keyboard.SLASH = pyglet.window.key.SLASH
        Keyboard._0 = pyglet.window.key._0
        Keyboard._1 = pyglet.window.key._1
        Keyboard._2 = pyglet.window.key._2
        Keyboard._3 = pyglet.window.key._3
        Keyboard._4 = pyglet.window.key._4
        Keyboard._5 = pyglet.window.key._5
        Keyboard._6 = pyglet.window.key._6
        Keyboard._7 = pyglet.window.key._7
        Keyboard._8 = pyglet.window.key._8
        Keyboard._9 = pyglet.window.key._9
        Keyboard.COLON = pyglet.window.key.COLON
        Keyboard.SEMICOLON = pyglet.window.key.SEMICOLON
        Keyboard.LESS = pyglet.window.key.LESS
        Keyboard.EQUAL = pyglet.window.key.EQUAL
        Keyboard.GREATER = pyglet.window.key.GREATER
        Keyboard.QUESTION = pyglet.window.key.QUESTION
        Keyboard.AT = pyglet.window.key.AT
        Keyboard.BRACKETLEFT = pyglet.window.key.BRACKETLEFT
        Keyboard.BACKSLASH = pyglet.window.key.BACKSLASH
        Keyboard.BRACKETRIGHT = pyglet.window.key.BRACKETRIGHT
        Keyboard.ASCIICIRCUM = pyglet.window.key.ASCIICIRCUM
        Keyboard.UNDERSCORE = pyglet.window.key.UNDERSCORE
        Keyboard.GRAVE = pyglet.window.key.GRAVE
        Keyboard.QUOTELEFT = pyglet.window.key.QUOTELEFT
        Keyboard.A = pyglet.window.key.A
        Keyboard.B = pyglet.window.key.B
        Keyboard.C = pyglet.window.key.C
        Keyboard.D = pyglet.window.key.D
        Keyboard.E = pyglet.window.key.E
        Keyboard.F = pyglet.window.key.F
        Keyboard.G = pyglet.window.key.G
        Keyboard.H = pyglet.window.key.H
        Keyboard.I = pyglet.window.key.I
        Keyboard.J = pyglet.window.key.J
        Keyboard.K = pyglet.window.key.K
        Keyboard.L = pyglet.window.key.L
        Keyboard.M = pyglet.window.key.M
        Keyboard.N = pyglet.window.key.N
        Keyboard.O = pyglet.window.key.O
        Keyboard.P = pyglet.window.key.P
        Keyboard.Q = pyglet.window.key.Q
        Keyboard.R = pyglet.window.key.R
        Keyboard.S = pyglet.window.key.S
        Keyboard.T = pyglet.window.key.T
        Keyboard.U = pyglet.window.key.U
        Keyboard.V = pyglet.window.key.V
        Keyboard.W = pyglet.window.key.W
        Keyboard.X = pyglet.window.key.X
        Keyboard.Y = pyglet.window.key.Y
        Keyboard.Z = pyglet.window.key.Z
        Keyboard.BRACELEFT = pyglet.window.key.BRACELEFT
        Keyboard.BAR = pyglet.window.key.BAR
        Keyboard.BRACERIGHT = pyglet.window.key.BRACERIGHT

        self.key_pressed = dict()

        for symbol in Keyboard.__dict__:
            self.key_pressed[Keyboard.__dict__[symbol]] = False

        self.valid = True

    def set_window_title(self, title):
        self.window.set_caption(title)

    def change_resolution(self, width, height, full_screen, resize_scene=True):
        changed = False
        if 0 < width and width != self.width:
            self.width = width
            changed = True
        if 0 < height and height != self.height:
            self.height = height
            changed = True

        if full_screen != self.full_screen:
            changed = True

        if changed:
            if full_screen:
                self.window.set_fullscreen(True)
                # cannot change screen size in fullscreen, fit to background screen size.
                self.width, self.height = self.window.get_size()
            elif not full_screen and self.full_screen:
                self.window.set_fullscreen(False)
                self.window.set_size(self.width, self.height)
            elif not full_screen and not self.full_screen:
                self.window.set_fullscreen(False)
                self.window.set_size(self.width, self.height)
            self.full_screen = full_screen

        if resize_scene:
            self.core_manager.renderer.resizeScene(self.width, self.height)
        self.core_manager.notify_change_resolution((self.width, self.height, self.full_screen))

    def on_resize(self, width, height):
        self.video_resized = True
        self.width = width
        self.height = height
        self.core_manager.update_event(Event.VIDEORESIZE, (width, height, self.full_screen))
        return pyglet.event.EVENT_HANDLED

    def on_draw(self):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_pos[0] = x
        self.mouse_pos[1] = y

    def on_mouse_press(self, x, y, button, modifiers):
        self.mouse_pos[0] = x
        self.mouse_pos[1] = y
        if button == pyglet.window.mouse.LEFT:
            self.mouse_btn_l = True
        elif button == pyglet.window.mouse.MIDDLE:
            self.mouse_btn_m = True
        elif button == pyglet.window.mouse.RIGHT:
            self.mouse_btn_r = True

    def on_mouse_release(self, x, y, button, modifiers):
        self.mouse_pos[0] = x
        self.mouse_pos[1] = y
        if button == pyglet.window.mouse.LEFT:
            self.mouse_btn_l = False
        elif button == pyglet.window.mouse.MIDDLE:
            self.mouse_btn_m = False
        elif button == pyglet.window.mouse.RIGHT:
            self.mouse_btn_r = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_pos[0] = x
        self.mouse_pos[1] = y

    def on_mouse_enter(self, x, y):
        if self.video_resized:
            self.resize_scene_to_window()
            self.video_resized = False

    def on_mouse_leave(self, x, y):
        pass

    def on_key_press(self, symbol, modifiers):
        self.key_pressed[symbol] = True
        self.core_manager.update_event(Event.KEYDOWN, symbol)

    def on_key_release(self, symbol, modifiers):
        self.key_pressed[symbol] = False

    def get_keyboard_pressed(self):
        return self.key_pressed

    def get_mouse_pressed(self):
        return self.mouse_btn_l, self.mouse_btn_m, self.mouse_btn_r

    def flip(self):
        self.window.flip()

    def run(self):
        self.running = True
        while self.running:
            pyglet.clock.tick()
            # for self.window in pyglet.app.windows:
            self.mouse_pos_old[...] = self.mouse_pos

            self.window.switch_to()

            # update event
            self.window.dispatch_events()
            # self.window.dispatch_event('on_draw')

            self.mouse_delta[...] = self.mouse_pos - self.mouse_pos_old
            self.core_manager.update()

    def close(self):
        self.running = False

    def quit(self):
        self.window.close()
