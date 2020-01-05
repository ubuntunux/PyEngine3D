import os

import numpy as np

from PyEngine3D.Utilities import *
from PyEngine3D.Common import logger, log_level, COMMAND


class GameBackNames:
    PYGLET = "pyglet"
    PYGAME = "pygame"
    COUNT = 2


class Event(AutoEnum):
    QUIT = ()
    VIDEORESIZE = ()
    KEYDOWN = ()
    KEYUP = ()
    TEXT = ()
    MOUSE_BUTTON_DOWN = ()
    MOUSE_BUTTON_UP = ()
    MOUSE_MOVE = ()


class InputMode(AutoEnum):
    NONE = ()
    GAME_PLAY = ()
    EDIT_OBJECT_TRANSFORM = ()


class Keyboard:
    # ASCII commands
    BACKSPACE = ()
    TAB = ()
    LINEFEED = ()
    CLEAR = ()
    RETURN = ()
    ENTER = ()
    PAUSE = ()
    SCROLLLOCK = ()
    SYSREQ = ()
    ESCAPE = ()
    SPACE = ()

    # Cursor control and motion
    HOME = ()
    LEFT = ()
    UP = ()
    RIGHT = ()
    DOWN = ()
    PAGEUP = ()
    PAGEDOWN = ()
    END = ()
    BEGIN = ()

    # Misc functions
    DELETE = ()
    SELECT = ()
    PRINT = ()
    EXECUTE = ()
    INSERT = ()
    UNDO = ()
    REDO = ()
    MENU = ()
    FIND = ()
    CANCEL = ()
    HELP = ()
    BREAK = ()
    MODESWITCH = ()
    SCRIPTSWITCH = ()
    FUNCTION = ()

    # Number pad
    NUMLOCK = ()
    NUM_SPACE = ()
    NUM_TAB = ()
    NUM_ENTER = ()
    NUM_F1 = ()
    NUM_F2 = ()
    NUM_F3 = ()
    NUM_F4 = ()
    NUM_HOME = ()
    NUM_LEFT = ()
    NUM_UP = ()
    NUM_RIGHT = ()
    NUM_DOWN = ()
    NUM_PRIOR = ()
    NUM_PAGE_UP = ()
    NUM_NEXT = ()
    NUM_PAGE_DOWN = ()
    NUM_END = ()
    NUM_BEGIN = ()
    NUM_INSERT = ()
    NUM_DELETE = ()
    NUM_EQUAL = ()
    NUM_MULTIPLY = ()
    NUM_ADD = ()
    NUM_SEPARATOR = ()
    NUM_SUBTRACT = ()
    NUM_DECIMAL = ()
    NUM_DIVIDE = ()

    NUM_0 = ()
    NUM_1 = ()
    NUM_2 = ()
    NUM_3 = ()
    NUM_4 = ()
    NUM_5 = ()
    NUM_6 = ()
    NUM_7 = ()
    NUM_8 = ()
    NUM_9 = ()

    # Function keys
    F1 = ()
    F2 = ()
    F3 = ()
    F4 = ()
    F5 = ()
    F6 = ()
    F7 = ()
    F8 = ()
    F9 = ()
    F10 = ()
    F11 = ()
    F12 = ()
    F13 = ()
    F14 = ()
    F15 = ()
    F16 = ()
    F17 = ()
    F18 = ()
    F19 = ()
    F20 = ()

    # Modifiers
    LSHIFT = ()
    RSHIFT = ()
    LCTRL = ()
    RCTRL = ()
    CAPSLOCK = ()
    LMETA = ()
    RMETA = ()
    LALT = ()
    RALT = ()
    LWINDOWS = ()
    RWINDOWS = ()
    LCOMMAND = ()
    RCOMMAND = ()
    LOPTION = ()
    ROPTION = ()

    # Latin-1
    SPACE = ()
    EXCLAMATION = ()
    DOUBLEQUOTE = ()
    HASH = ()
    POUND = ()
    DOLLAR = ()
    PERCENT = ()
    AMPERSAND = ()
    APOSTROPHE = ()
    PARENLEFT = ()
    PARENRIGHT = ()
    ASTERISK = ()
    PLUS = ()
    COMMA = ()
    MINUS = ()
    PERIOD = ()
    SLASH = ()
    BACKQUOTE = ()
    _0 = ()
    _1 = ()
    _2 = ()
    _3 = ()
    _4 = ()
    _5 = ()
    _6 = ()
    _7 = ()
    _8 = ()
    _9 = ()
    COLON = ()
    SEMICOLON = ()
    LESS = ()
    EQUAL = ()
    GREATER = ()
    QUESTION = ()
    AT = ()
    BRACKETLEFT = ()
    BACKSLASH = ()
    BRACKETRIGHT = ()
    ASCIICIRCUM = ()
    UNDERSCORE = ()
    GRAVE = ()
    QUOTELEFT = ()
    A = ()
    B = ()
    C = ()
    D = ()
    E = ()
    F = ()
    G = ()
    H = ()
    I = ()
    J = ()
    K = ()
    L = ()
    M = ()
    N = ()
    O = ()
    P = ()
    Q = ()
    R = ()
    S = ()
    T = ()
    U = ()
    V = ()
    W = ()
    X = ()
    Y = ()
    Z = ()
    BRACELEFT = ()
    BAR = ()
    BRACERIGHT = ()
    ASCIITILDE = ()


class GameBackend:
    def __init__(self, core_manager):
        self.running = False
        self.valid = False
        self.core_manager = core_manager

        self.width = 0
        self.height = 0
        self.half_width = 0
        self.half_height = 0
        self.goal_width = 0
        self.goal_height = 0
        self.screen_width = 0
        self.screen_height = 0
        self.aspect = 1.0
        self.full_screen = False
        self.is_play_mode = False
        self.input_mode = InputMode.NONE

        self.mouse_grab = False
        self.mouse_pos = np.zeros(2)
        self.mouse_pos_old = np.zeros(2)
        self.mouse_delta = np.zeros(2)
        self.wheel_up = False
        self.wheel_down = False
        self.btn_l_down = False
        self.btn_m_down = False
        self.btn_r_down = False
        self.btn_l_pressed = False
        self.btn_m_pressed = False
        self.btn_r_pressed = False
        self.btn_l_up = False
        self.btn_m_up = False
        self.btn_r_up = False

        self.text = ''
        self.keyboard_down = False
        self.keyboard_pressed = False
        self.keyboard_up = False

        self.key_pressed = dict()
        self.key_released = dict()

    def get_input_mode(self):
        return self.input_mode

    def set_input_mode(self, input_mode):
        self.input_mode = input_mode

    def get_mouse_grab(self):
        return self.mouse_grab

    def set_mouse_grab(self, grab):
        self.mouse_grab = grab

    def toggle_mouse_grab(self):
        self.set_mouse_grab(not self.get_mouse_grab())

    def get_mouse_down(self):
        return self.btn_l_down, self.btn_m_down, self.btn_r_down

    def get_mouse_pressed(self):
        return self.btn_l_pressed, self.btn_m_pressed, self.btn_r_pressed

    def get_mouse_up(self):
        return self.btn_l_up, self.btn_m_up, self.btn_r_up

    def get_keyboard_released(self):
        return self.key_released

    def set_window_info(self, width, height, full_screen):
        changed = False

        if full_screen:
            width = self.screen_width
            height = self.screen_height

        if 0 < width != self.width:
            self.width = width
            self.half_width = width / 2
            changed = True

        if 0 < height != self.height:
            self.height = height
            self.half_height = height / 2
            changed = True

        if 0 < width and 0 < height:
            self.aspect = float(width) / float(height)

        if full_screen != self.full_screen:
            self.full_screen = full_screen
            changed = True

        logger.info("Set Window Info : %d x %d Full Screen (%s)" % (width, height, full_screen))

        return changed

    def create_window(self, width, height, fullscreen):
        if self.set_window_info(width, height, fullscreen):
            self.do_change_resolution()

    def change_resolution(self, width, height, full_screen):
        if self.set_window_info(width, height, full_screen):
            self.do_change_resolution()
            self.reset_screen()

    def reset_screen(self):
        # update perspective and ortho
        self.core_manager.scene_manager.update_camera_projection_matrix(aspect=self.aspect)

        # reset viewport
        self.core_manager.viewport_manager.resize_viewport(self.width, self.height)

        # reset frame buffers and render targets
        self.core_manager.renderer.reset_renderer()

    def resize_scene_to_window(self):
        if self.set_window_info(self.goal_width, self.goal_height, self.full_screen):
            self.reset_screen()

    def create_sound_listner(self):
        pass

    def create_sound(self, filepath):
        pass

    def play_sound(self, sound, loop=False, volume=1.0, position=None):
        pass

    def stop_sound(self, sound):
        pass

    def is_sound_playing(self, sound):
        pass
