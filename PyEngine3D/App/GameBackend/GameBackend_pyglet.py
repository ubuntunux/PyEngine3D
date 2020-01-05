import os

import numpy as np

import pyglet
from pyglet import info
from pyglet import window
from pyglet.window import key
from pyglet.window import mouse
from pyglet.gl import *

from PyEngine3D.Common import logger, INITIAL_WIDTH, INITIAL_HEIGHT, SOUND_DISTANCE_RATIO
from .GameBackend import GameBackend, Keyboard, Event


class PyGlet(GameBackend):
    enable_font = False
    enable_keyboard = False
    enable_mouse = False

    def __init__(self, core_manager):
        GameBackend.__init__(self, core_manager)

        logger.info('GameBackend : pyglet %s' % pyglet.version)

        # os.environ['PYGLET_DEBUG_GL'] = '1'
        config = Config(double_buffer=True, )

        # get default screen
        try:
            platform = pyglet.window.get_platform()
            display = platform.get_default_display()
            screen = display.get_default_screen()
        except AttributeError as e:
            screen = pyglet.canvas.Display().get_default_screen()

        self.screen_width = screen.width
        self.screen_height = screen.height

        # Ubuntu Vsync Off : NVidia X Server Setting -> OpenGL Setting -> Sync To VBlank ( Off )
        self.window = window.Window(width=INITIAL_WIDTH, height=INITIAL_HEIGHT, config=config, resizable=True, vsync=False)

        self.set_mouse_grab(self.mouse_grab)

        # for debbug
        # self.window.push_handlers(window.event.WindowEventLogger())

        # show system info
        # pyglet.info.dump()

        # listen for draw and resize events
        self.window.push_handlers(
            on_draw=self.on_draw,
            on_resize=self.on_resize,
            on_text=self.on_text,
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
        Keyboard.BACKSPACE = window.key.BACKSPACE
        Keyboard.TAB = window.key.TAB
        Keyboard.LINEFEED = window.key.LINEFEED
        Keyboard.CLEAR = window.key.CLEAR
        Keyboard.RETURN = window.key.RETURN
        Keyboard.ENTER = window.key.ENTER
        Keyboard.PAUSE = window.key.PAUSE
        Keyboard.SCROLLLOCK = window.key.SCROLLLOCK
        Keyboard.SYSREQ = window.key.SYSREQ
        Keyboard.ESCAPE = window.key.ESCAPE
        Keyboard.SPACE = window.key.SPACE

        # Cursor control and motion
        Keyboard.HOME = window.key.HOME
        Keyboard.LEFT = window.key.LEFT
        Keyboard.UP = window.key.UP
        Keyboard.RIGHT = window.key.RIGHT
        Keyboard.DOWN = window.key.DOWN
        Keyboard.PAGEUP = window.key.PAGEUP
        Keyboard.PAGEDOWN = window.key.PAGEDOWN
        Keyboard.END = window.key.END
        Keyboard.BEGIN = window.key.BEGIN

        # Misc functions
        Keyboard.DELETE = window.key.DELETE
        Keyboard.SELECT = window.key.SELECT
        Keyboard.PRINT = window.key.PRINT
        Keyboard.EXECUTE = window.key.EXECUTE
        Keyboard.INSERT = window.key.INSERT
        Keyboard.UNDO = window.key.UNDO
        Keyboard.REDO = window.key.REDO
        Keyboard.MENU = window.key.MENU
        Keyboard.FIND = window.key.FIND
        Keyboard.CANCEL = window.key.CANCEL
        Keyboard.HELP = window.key.HELP
        Keyboard.BREAK = window.key.BREAK
        Keyboard.MODESWITCH = window.key.MODESWITCH
        Keyboard.SCRIPTSWITCH = window.key.SCRIPTSWITCH
        Keyboard.FUNCTION = window.key.FUNCTION

        # Number pad
        Keyboard.NUMLOCK = window.key.NUMLOCK
        Keyboard.NUM_SPACE = window.key.NUM_SPACE
        Keyboard.NUM_TAB = window.key.NUM_TAB
        Keyboard.NUM_ENTER = window.key.NUM_ENTER
        Keyboard.NUM_F1 = window.key.NUM_F1
        Keyboard.NUM_F2 = window.key.NUM_F2
        Keyboard.NUM_F3 = window.key.NUM_F3
        Keyboard.NUM_F4 = window.key.NUM_F4
        Keyboard.NUM_HOME = window.key.NUM_HOME
        Keyboard.NUM_LEFT = window.key.NUM_LEFT
        Keyboard.NUM_UP = window.key.NUM_UP
        Keyboard.NUM_RIGHT = window.key.NUM_RIGHT
        Keyboard.NUM_DOWN = window.key.NUM_DOWN
        Keyboard.NUM_PRIOR = window.key.NUM_PRIOR
        Keyboard.NUM_PAGE_UP = window.key.NUM_PAGE_UP
        Keyboard.NUM_NEXT = window.key.NUM_NEXT
        Keyboard.NUM_PAGE_DOWN = window.key.NUM_PAGE_DOWN
        Keyboard.NUM_END = window.key.NUM_END
        Keyboard.NUM_BEGIN = window.key.NUM_BEGIN
        Keyboard.NUM_INSERT = window.key.NUM_INSERT
        Keyboard.NUM_DELETE = window.key.NUM_DELETE
        Keyboard.NUM_EQUAL = window.key.NUM_EQUAL
        Keyboard.NUM_MULTIPLY = window.key.NUM_MULTIPLY
        Keyboard.NUM_ADD = window.key.NUM_ADD
        Keyboard.NUM_SEPARATOR = window.key.NUM_SEPARATOR
        Keyboard.NUM_SUBTRACT = window.key.NUM_SUBTRACT
        Keyboard.NUM_DECIMAL = window.key.NUM_DECIMAL
        Keyboard.NUM_DIVIDE = window.key.NUM_DIVIDE

        Keyboard.NUM_0 = window.key.NUM_0
        Keyboard.NUM_1 = window.key.NUM_1
        Keyboard.NUM_2 = window.key.NUM_2
        Keyboard.NUM_3 = window.key.NUM_3
        Keyboard.NUM_4 = window.key.NUM_4
        Keyboard.NUM_5 = window.key.NUM_5
        Keyboard.NUM_6 = window.key.NUM_6
        Keyboard.NUM_7 = window.key.NUM_7
        Keyboard.NUM_8 = window.key.NUM_8
        Keyboard.NUM_9 = window.key.NUM_9

        # Function keys
        Keyboard.F1 = window.key.F1
        Keyboard.F2 = window.key.F2
        Keyboard.F3 = window.key.F3
        Keyboard.F4 = window.key.F4
        Keyboard.F5 = window.key.F5
        Keyboard.F6 = window.key.F6
        Keyboard.F7 = window.key.F7
        Keyboard.F8 = window.key.F8
        Keyboard.F9 = window.key.F9
        Keyboard.F10 = window.key.F10
        Keyboard.F11 = window.key.F11
        Keyboard.F12 = window.key.F12
        Keyboard.F13 = window.key.F13
        Keyboard.F14 = window.key.F14
        Keyboard.F15 = window.key.F15
        Keyboard.F16 = window.key.F16
        Keyboard.F17 = window.key.F17
        Keyboard.F18 = window.key.F18
        Keyboard.F19 = window.key.F19
        Keyboard.F20 = window.key.F20

        # Modifiers
        Keyboard.LSHIFT = window.key.LSHIFT
        Keyboard.RSHIFT = window.key.RSHIFT
        Keyboard.LCTRL = window.key.LCTRL
        Keyboard.RCTRL = window.key.RCTRL
        Keyboard.CAPSLOCK = window.key.CAPSLOCK
        Keyboard.LMETA = window.key.LMETA
        Keyboard.RMETA = window.key.RMETA
        Keyboard.LALT = window.key.LALT
        Keyboard.RALT = window.key.RALT
        Keyboard.LWINDOWS = window.key.LWINDOWS
        Keyboard.RWINDOWS = window.key.RWINDOWS
        Keyboard.LCOMMAND = window.key.LCOMMAND
        Keyboard.RCOMMAND = window.key.RCOMMAND
        Keyboard.LOPTION = window.key.LOPTION
        Keyboard.ROPTION = window.key.ROPTION

        # Latin-1
        Keyboard.SPACE = window.key.SPACE
        Keyboard.EXCLAMATION = window.key.EXCLAMATION
        Keyboard.DOUBLEQUOTE = window.key.DOUBLEQUOTE
        Keyboard.HASH = window.key.HASH
        Keyboard.POUND = window.key.POUND
        Keyboard.DOLLAR = window.key.DOLLAR
        Keyboard.PERCENT = window.key.PERCENT
        Keyboard.AMPERSAND = window.key.AMPERSAND
        Keyboard.APOSTROPHE = window.key.APOSTROPHE
        Keyboard.PARENLEFT = window.key.PARENLEFT
        Keyboard.PARENRIGHT = window.key.PARENRIGHT
        Keyboard.ASTERISK = window.key.ASTERISK
        Keyboard.PLUS = window.key.PLUS
        Keyboard.COMMA = window.key.COMMA
        Keyboard.MINUS = window.key.MINUS
        Keyboard.PERIOD = window.key.PERIOD
        Keyboard.SLASH = window.key.SLASH
        Keyboard.BACKQUOTE = window.key.QUOTELEFT
        Keyboard._0 = window.key._0
        Keyboard._1 = window.key._1
        Keyboard._2 = window.key._2
        Keyboard._3 = window.key._3
        Keyboard._4 = window.key._4
        Keyboard._5 = window.key._5
        Keyboard._6 = window.key._6
        Keyboard._7 = window.key._7
        Keyboard._8 = window.key._8
        Keyboard._9 = window.key._9
        Keyboard.COLON = window.key.COLON
        Keyboard.SEMICOLON = window.key.SEMICOLON
        Keyboard.LESS = window.key.LESS
        Keyboard.EQUAL = window.key.EQUAL
        Keyboard.GREATER = window.key.GREATER
        Keyboard.QUESTION = window.key.QUESTION
        Keyboard.AT = window.key.AT
        Keyboard.BRACKETLEFT = window.key.BRACKETLEFT
        Keyboard.BACKSLASH = window.key.BACKSLASH
        Keyboard.BRACKETRIGHT = window.key.BRACKETRIGHT
        Keyboard.ASCIICIRCUM = window.key.ASCIICIRCUM
        Keyboard.UNDERSCORE = window.key.UNDERSCORE
        Keyboard.GRAVE = window.key.GRAVE
        Keyboard.QUOTELEFT = window.key.QUOTELEFT
        Keyboard.A = window.key.A
        Keyboard.B = window.key.B
        Keyboard.C = window.key.C
        Keyboard.D = window.key.D
        Keyboard.E = window.key.E
        Keyboard.F = window.key.F
        Keyboard.G = window.key.G
        Keyboard.H = window.key.H
        Keyboard.I = window.key.I
        Keyboard.J = window.key.J
        Keyboard.K = window.key.K
        Keyboard.L = window.key.L
        Keyboard.M = window.key.M
        Keyboard.N = window.key.N
        Keyboard.O = window.key.O
        Keyboard.P = window.key.P
        Keyboard.Q = window.key.Q
        Keyboard.R = window.key.R
        Keyboard.S = window.key.S
        Keyboard.T = window.key.T
        Keyboard.U = window.key.U
        Keyboard.V = window.key.V
        Keyboard.W = window.key.W
        Keyboard.X = window.key.X
        Keyboard.Y = window.key.Y
        Keyboard.Z = window.key.Z
        Keyboard.BRACELEFT = window.key.BRACELEFT
        Keyboard.BAR = window.key.BAR
        Keyboard.BRACERIGHT = window.key.BRACERIGHT

        for symbol in Keyboard.__dict__:
            self.key_pressed[Keyboard.__dict__[symbol]] = False

        self.valid = True

    def set_mouse_grab(self, grab):
        GameBackend.set_mouse_grab(self, grab)
        self.window.set_exclusive_mouse(grab)

    def set_window_title(self, title):
        self.window.set_caption(title)

    def set_mouse_visible(self, visible):
        self.window.set_mouse_visible(visible)

    def do_change_resolution(self):
        if self.full_screen:
            self.window.set_fullscreen(fullscreen=True)
        else:
            self.window.set_fullscreen(width=self.width, height=self.height, fullscreen=False)
            # self.window.set_size(self.width, self.height)

    def update_event(self):
        if self.get_mouse_grab():
            self.mouse_pos_old[0] = self.width / 2
            self.mouse_pos_old[1] = self.height / 2
        else:
            self.mouse_pos_old[...] = self.mouse_pos
        self.mouse_delta[0] = 0.0
        self.mouse_delta[1] = 0.0

        self.btn_l_down = False
        self.btn_m_down = False
        self.btn_r_down = False
        self.btn_l_up = False
        self.btn_m_up = False
        self.btn_r_up = False
        self.keyboard_down = False
        self.keyboard_up = False
        self.key_released.clear()

        self.window.switch_to()

        # update event
        self.window.dispatch_events()
        # self.window.dispatch_event('on_draw')

        if not self.mouse_grab:
            self.mouse_delta[0] = self.mouse_pos[0] - self.mouse_pos_old[0]
            self.mouse_delta[1] = self.mouse_pos[1] - self.mouse_pos_old[1]

    def on_resize(self, width, height):
        self.goal_width = width
        self.goal_height = height
        self.core_manager.update_event(Event.VIDEORESIZE, (width, height, self.full_screen))
        return pyglet.event.EVENT_HANDLED

    def on_draw(self):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_pos[0] = x
        self.mouse_pos[1] = y
        if self.mouse_grab:
            self.mouse_delta[0] += x - self.half_width  # dx
            self.mouse_delta[1] += y - self.half_height  # dy
        self.core_manager.update_event(Event.MOUSE_MOVE)

    def on_mouse_press(self, x, y, button, modifiers):
        self.mouse_pos[0] = x
        self.mouse_pos[1] = y
        if button == window.mouse.LEFT:
            self.btn_l_down = True
            self.btn_l_pressed = True
        elif button == window.mouse.MIDDLE:
            self.btn_m_down = True
            self.btn_m_pressed = True
        elif button == window.mouse.RIGHT:
            self.btn_r_down = True
            self.btn_r_pressed = True
        self.core_manager.update_event(Event.MOUSE_BUTTON_DOWN)

    def on_mouse_release(self, x, y, button, modifiers):
        self.mouse_pos[0] = x
        self.mouse_pos[1] = y
        if button == window.mouse.LEFT:
            self.btn_l_up = True
            self.btn_l_pressed = False
        elif button == window.mouse.MIDDLE:
            self.btn_m_up = True
            self.btn_m_pressed = False
        elif button == window.mouse.RIGHT:
            self.btn_r_up = True
            self.btn_r_pressed = False
        self.core_manager.update_event(Event.MOUSE_BUTTON_UP)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_pos[0] = x
        self.mouse_pos[1] = y
        if self.mouse_grab:
            self.mouse_delta[0] += x - self.half_width  # dx
            self.mouse_delta[1] += y - self.half_height  # dy
        self.core_manager.update_event(Event.MOUSE_MOVE)

    def on_mouse_enter(self, x, y):
        pass

    def on_mouse_leave(self, x, y):
        pass

    def on_text(self, text):
        self.text = text
        self.core_manager.update_event(Event.TEXT, text)

    def on_key_press(self, symbol, modifiers):
        self.keyboard_down = True
        self.keyboard_pressed = True
        self.key_pressed[symbol] = True
        self.key_released[symbol] = False
        self.core_manager.update_event(Event.KEYDOWN, symbol)

    def on_key_release(self, symbol, modifiers):
        self.text = ''
        self.keyboard_up = True
        self.keyboard_pressed = False
        self.key_pressed[symbol] = False
        self.key_released[symbol] = True
        self.core_manager.update_event(Event.KEYUP, symbol)

    def get_keyboard_pressed(self):
        return self.key_pressed

    def get_mouse_pressed(self):
        return self.btn_l_pressed, self.btn_m_pressed, self.btn_r_pressed

    def flip(self):
        self.window.flip()

    def run(self):
        self.running = True
        while self.running:
            pyglet.clock.tick()

            self.update_event()

            self.core_manager.update()

    def close(self):
        self.running = False

    def quit(self):
        self.window.close()

    def create_sound_listner(self):
        return pyglet.media.get_audio_driver().get_listener()

    def create_sound(self, filepath):
        sound = pyglet.media.load(filepath, streaming=False)
        return sound

    def play_sound(self, sound, loop=False, volume=1.0, position=None):
        sound_player = sound.play()
        sound_player.loop = loop
        sound_player.volume = volume

        if position is not None:
            sound_player.position = tuple(position * SOUND_DISTANCE_RATIO)

        if loop:
            pyglet.clock.schedule_interval(lambda dt: sound_player.dispatch_event("on_eos"), sound_player.source.duration)
        else:
            pyglet.clock.schedule_once(lambda dt: sound_player.dispatch_event("on_eos"), sound_player.source.duration)

        return sound_player

    def pause_sound(self, sound_player):
        sound_player.pause()

    def stop_sound(self, sound_player):
        sound_player.delete()

    def is_sound_playing(self, sound_player):
        return sound_player._playing
