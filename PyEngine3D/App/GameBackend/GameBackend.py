import os

import numpy as np

from PyEngine3D.Utilities import *
from PyEngine3D.Common import logger, log_level, COMMAND


class Event(AutoEnum):
    QUIT = ()
    VIDEORESIZE = ()
    KEYDOWN = ()


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
        logger.info("Run game backend : " + self.__class__.__name__)

        self.running = False
        self.valid = False
        self.core_manager = core_manager

        self.width = 0
        self.height = 0
        self.full_screen = False

        self.video_resized = False

        self.mouse_pos = np.zeros(2)
        self.mouse_pos_old = np.zeros(2)
        self.mouse_delta = np.zeros(2)
        self.wheel_up = False
        self.wheel_down = False
        self.mouse_btn_l = False
        self.mouse_btn_m = False
        self.mouse_btn_r = False

    def resize_scene_to_window(self):
        self.core_manager.renderer.resizeScene(self.width, self.height)

