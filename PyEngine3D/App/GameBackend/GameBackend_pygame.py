import os

import pygame
from pygame.locals import *

from PyEngine3D.Common import logger
from .GameBackend import GameBackend, Keyboard, Event


class PyGame(GameBackend):
    def __init__(self, core_manager):
        GameBackend.__init__(self, core_manager)

        logger.info('GameBackend : pygame %s' % pygame.__version__)

        # centered window
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.mixer.pre_init(44100, -16, 2, 4096)
        pygame.mixer.init()
        pygame.init()

        self.screen_width = pygame.display.Info().current_w
        self.screen_height = pygame.display.Info().current_h

        self.set_mouse_grab(self.get_mouse_grab())

        pygame.font.init()
        if not pygame.font.get_init():
            logger.error('Could not render font.')
            return

        # ASCII commands
        Keyboard.BACKSPACE = K_BACKSPACE
        Keyboard.TAB = K_TAB
        # Keyboard.LINEFEED = K_LINEFEED
        Keyboard.CLEAR = K_CLEAR
        Keyboard.RETURN = K_RETURN
        Keyboard.ENTER = K_KP_ENTER
        Keyboard.PAUSE = K_PAUSE
        Keyboard.SCROLLLOCK = K_SCROLLOCK
        Keyboard.SYSREQ = K_SYSREQ
        Keyboard.ESCAPE = K_ESCAPE
        Keyboard.SPACE = K_SPACE

        # Cursor control and motion
        Keyboard.HOME = K_HOME
        Keyboard.LEFT = K_LEFT
        Keyboard.UP = K_UP
        Keyboard.RIGHT = K_RIGHT
        Keyboard.DOWN = K_DOWN
        Keyboard.PAGEUP = K_PAGEUP
        Keyboard.PAGEDOWN = K_PAGEDOWN
        Keyboard.END = K_END
        # Keyboard.BEGIN = K_BEGIN

        # Misc functions
        Keyboard.DELETE = K_DELETE
        # Keyboard.SELECT = K_SELECT
        Keyboard.PRINT = K_PRINT
        # Keyboard.EXECUTE = K_EXECUTE
        Keyboard.INSERT = K_INSERT
        # Keyboard.UNDO = K_UNDO
        # Keyboard.REDO = K_REDO
        Keyboard.MENU = K_MENU
        # Keyboard.FIND = K_FIND
        # Keyboard.CANCEL = K_CANCEL
        Keyboard.HELP = K_HELP
        Keyboard.BREAK = K_BREAK
        # Keyboard.MODESWITCH = K_MODESWITCH
        # Keyboard.SCRIPTSWITCH = K_SCRIPTSWITCH
        # Keyboard.FUNCTION = K_FUNCTION

        # Number pad
        Keyboard.NUMLOCK = K_NUMLOCK
        # Keyboard.NUM_SPACE = K_NUM_SPACE
        # Keyboard.NUM_TAB = K_NUM_TAB
        # Keyboard.NUM_ENTER = K_NUM_ENTER
        # Keyboard.NUM_F1 = K_NUM_F1
        # Keyboard.NUM_F2 = K_NUM_F2
        # Keyboard.NUM_F3 = K_NUM_F3
        # Keyboard.NUM_F4 = K_NUM_F4
        # Keyboard.NUM_HOME = K_NUM_HOME
        # Keyboard.NUM_LEFT = K_NUM_LEFT
        # Keyboard.NUM_UP = K_NUM_UP
        # Keyboard.NUM_RIGHT = K_NUM_RIGHT
        # Keyboard.NUM_DOWN = K_NUM_DOWN
        # Keyboard.NUM_PRIOR = K_NUM_PRIOR
        # Keyboard.NUM_PAGE_UP = K_NUM_PAGE_UP
        # Keyboard.NUM_NEXT = K_NUM_NEXT
        # Keyboard.NUM_PAGE_DOWN = K_NUM_PAGE_DOWN
        # Keyboard.NUM_END = K_NUM_END
        # Keyboard.NUM_BEGIN = K_NUM_BEGIN
        # Keyboard.NUM_INSERT = K_NUM_INSERT
        # Keyboard.NUM_DELETE = K_NUM_DELETE
        # Keyboard.NUM_EQUAL = K_NUM_EQUAL
        # Keyboard.NUM_MULTIPLY = K_NUM_MULTIPLY
        # Keyboard.NUM_ADD = K_NUM_ADD
        # Keyboard.NUM_SEPARATOR = K_NUM_SEPARATOR
        # Keyboard.NUM_SUBTRACT = K_NUM_SUBTRACT
        # Keyboard.NUM_DECIMAL = K_NUM_DECIMAL
        # Keyboard.NUM_DIVIDE = K_NUM_DIVIDE

        # Keyboard.NUM_0 = K_NUM_0
        # Keyboard.NUM_1 = K_NUM_1
        # Keyboard.NUM_2 = K_NUM_2
        # Keyboard.NUM_3 = K_NUM_3
        # Keyboard.NUM_4 = K_NUM_4
        # Keyboard.NUM_5 = K_NUM_5
        # Keyboard.NUM_6 = K_NUM_6
        # Keyboard.NUM_7 = K_NUM_7
        # Keyboard.NUM_8 = K_NUM_8
        # Keyboard.NUM_9 = K_NUM_9

        # Function keys
        Keyboard.F1 = K_F1
        Keyboard.F2 = K_F2
        Keyboard.F3 = K_F3
        Keyboard.F4 = K_F4
        Keyboard.F5 = K_F5
        Keyboard.F6 = K_F6
        Keyboard.F7 = K_F7
        Keyboard.F8 = K_F8
        Keyboard.F9 = K_F9
        Keyboard.F10 = K_F10
        Keyboard.F11 = K_F11
        Keyboard.F12 = K_F12
        Keyboard.F13 = K_F13
        Keyboard.F14 = K_F14
        Keyboard.F15 = K_F15
        # Keyboard.F16 = K_F16
        # Keyboard.F17 = K_F17
        # Keyboard.F18 = K_F18
        # Keyboard.F19 = K_F19
        # Keyboard.F20 = K_F20

        # Modifiers
        Keyboard.LSHIFT = K_LSHIFT
        Keyboard.RSHIFT = K_RSHIFT
        Keyboard.LCTRL = K_LCTRL
        Keyboard.RCTRL = K_RCTRL
        Keyboard.CAPSLOCK = K_CAPSLOCK
        Keyboard.LMETA = K_LMETA
        Keyboard.RMETA = K_RMETA
        Keyboard.LALT = K_LALT
        Keyboard.RALT = K_RALT
        # Keyboard.LWINDOWS = K_LWINDOWS
        # Keyboard.RWINDOWS = K_RWINDOWS
        # Keyboard.LCOMMAND = K_LCOMMAND
        # Keyboard.RCOMMAND = K_RCOMMAND
        # Keyboard.LOPTION = K_LOPTION
        # Keyboard.ROPTION = K_ROPTION

        # Latin-1
        Keyboard.SPACE = K_SPACE
        # Keyboard.EXCLAMATION = K_EXCLAMATION
        # Keyboard.DOUBLEQUOTE = K_DOUBLEQUOTE
        Keyboard.HASH = K_HASH
        # Keyboard.POUND = K_POUND
        Keyboard.DOLLAR = K_DOLLAR
        # Keyboard.PERCENT = K_PERCENT
        Keyboard.AMPERSAND = K_AMPERSAND
        # Keyboard.APOSTROPHE = K_APOSTROPHE
        Keyboard.PARENLEFT = K_LEFTPAREN
        Keyboard.PARENRIGHT = K_RIGHTPAREN
        Keyboard.ASTERISK = K_ASTERISK
        Keyboard.PLUS = K_PLUS
        Keyboard.COMMA = K_COMMA
        Keyboard.MINUS = K_MINUS
        Keyboard.PERIOD = K_PERIOD
        Keyboard.SLASH = K_SLASH
        Keyboard.BACKQUOTE = K_BACKQUOTE
        Keyboard._0 = K_0
        Keyboard._1 = K_1
        Keyboard._2 = K_2
        Keyboard._3 = K_3
        Keyboard._4 = K_4
        Keyboard._5 = K_5
        Keyboard._6 = K_6
        Keyboard._7 = K_7
        Keyboard._8 = K_8
        Keyboard._9 = K_9
        Keyboard.COLON = K_COLON
        Keyboard.SEMICOLON = K_SEMICOLON
        Keyboard.LESS = K_LESS
        Keyboard.EQUAL = K_EQUALS
        Keyboard.GREATER = K_GREATER
        Keyboard.QUESTION = K_QUESTION
        Keyboard.AT = K_AT
        Keyboard.BRACKETLEFT = K_LEFTBRACKET
        Keyboard.BACKSLASH = K_BACKSLASH
        Keyboard.BRACKETRIGHT = K_RIGHTBRACKET
        # Keyboard.ASCIICIRCUM = K_ASCIICIRCUM
        Keyboard.UNDERSCORE = K_UNDERSCORE
        # Keyboard.GRAVE = K_GRAVE
        Keyboard.QUOTELEFT = K_QUOTE
        Keyboard.A = K_a
        Keyboard.B = K_b
        Keyboard.C = K_c
        Keyboard.D = K_d
        Keyboard.E = K_e
        Keyboard.F = K_f
        Keyboard.G = K_g
        Keyboard.H = K_h
        Keyboard.I = K_i
        Keyboard.J = K_j
        Keyboard.K = K_k
        Keyboard.L = K_l
        Keyboard.M = K_m
        Keyboard.N = K_n
        Keyboard.O = K_o
        Keyboard.P = K_p
        Keyboard.Q = K_q
        Keyboard.R = K_r
        Keyboard.S = K_s
        Keyboard.T = K_t
        Keyboard.U = K_u
        Keyboard.V = K_v
        Keyboard.W = K_w
        Keyboard.X = K_x
        Keyboard.Y = K_y
        Keyboard.Z = K_z
        # Keyboard.BRACELEFT = K_LEFTBRACE
        # Keyboard.BAR = K_BAR
        # Keyboard.BRACERIGHT = K_BRACERIGHT
        # Keyboard.ASCIITILDE = K_ASCIITILDEC

        for symbol in Keyboard.__dict__:
            self.key_pressed[Keyboard.__dict__[symbol]] = False

        self.valid = True

    def set_mouse_grab(self, grab):
        GameBackend.set_mouse_grab(self, grab)
        pygame.event.set_grab(grab)
        pygame.mouse.set_visible(not grab)

    def set_window_title(self, title):
        pygame.display.set_caption(title)

    def set_mouse_visible(self, visible):
        pygame.mouse.set_visible(visible)

    def do_change_resolution(self):
        option = OPENGL | DOUBLEBUF | HWPALETTE | HWSURFACE | RESIZABLE

        if self.full_screen:
            option |= FULLSCREEN

        pygame.display.set_mode((self.width, self.height), option)

    def update_event(self):
        if self.get_mouse_grab():
            self.mouse_pos_old[0] = self.width / 2
            self.mouse_pos_old[1] = self.height / 2
        else:
            self.mouse_pos_old[...] = self.mouse_pos

        self.btn_l_down = False
        self.btn_m_down = False
        self.btn_r_down = False
        self.btn_l_up = False
        self.btn_m_up = False
        self.btn_r_up = False
        self.wheel_up = False
        self.wheel_down = False
        self.keyboard_up = False
        self.keyboard_down = False
        self.key_released.clear()

        # Keyboard & Mouse Events
        for event in pygame.event.get():
            event_type = event.type

            if event_type == QUIT:
                self.core_manager.update_event(Event.QUIT)
            elif event_type == VIDEORESIZE:
                self.goal_width, self.goal_height = event.dict['size']
                self.core_manager.update_event(Event.VIDEORESIZE, (self.goal_width, self.goal_height, self.full_screen))
            elif event_type == KEYDOWN:
                self.text = event.unicode
                self.keyboard_down = True
                self.keyboard_pressed = True
                self.key_pressed[event.key] = True
                self.key_released[event.key] = False
                self.core_manager.update_event(Event.TEXT, event.unicode)
                self.core_manager.update_event(Event.KEYDOWN, event.key)
            elif event_type == KEYUP:
                self.text = ''
                self.keyboard_up = True
                self.keyboard_pressed = False
                self.key_pressed[event.key] = False
                self.key_released[event.key] = True
                self.core_manager.update_event(Event.KEYUP, event.key)
            elif event_type == MOUSEMOTION:
                self.mouse_pos[...] = pygame.mouse.get_pos()
                # invert - Y
                self.mouse_pos[1] = self.height - self.mouse_pos[1]
                self.core_manager.update_event(Event.MOUSE_MOVE)
            elif event_type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.btn_l_down = True
                    self.btn_l_pressed = True
                elif event.button == 2:
                    self.btn_m_down = True
                    self.btn_m_pressed = True
                elif event.button == 3:
                    self.btn_r_down = True
                    self.btn_r_pressed = True
                elif event.button == 4:
                    self.wheel_up = True
                elif event.button == 5:
                    self.wheel_down = True
                self.core_manager.update_event(Event.MOUSE_BUTTON_DOWN)
            elif event_type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.btn_l_up = True
                    self.btn_l_pressed = False
                elif event.button == 2:
                    self.btn_m_up = True
                    self.btn_m_pressed = False
                elif event.button == 3:
                    self.btn_r_up = True
                    self.btn_r_pressed = False
                elif event.button == 4:
                    self.wheel_up = False
                elif event.button == 5:
                    self.wheel_down = False
                self.core_manager.update_event(Event.MOUSE_BUTTON_UP)
        self.mouse_delta[...] = self.mouse_pos - self.mouse_pos_old

        if self.get_mouse_grab():
            pygame.mouse.set_pos([self.width / 2, self.height / 2])

    def get_keyboard_pressed(self):
        return pygame.key.get_pressed()

    def flip(self):
        pygame.display.flip()

    def run(self):
        self.running = True
        while self.running:
            self.update_event()
            self.core_manager.update()

    def close(self):
        self.running = False

    def quit(self):
        pygame.display.quit()
        pygame.quit()

    def create_sound_listner(self):
        return None

    def create_music(self, filepath, volume=1.0, loop=False):
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1 if loop else 0)

    def create_sound(self, filepath):
        sound = pygame.mixer.Sound(filepath)
        return sound

    def play_sound(self, sound, loop=False, volume=1.0, position=None):
        sound.play(1 if loop else 0)
        sound.set_volume(volume)
        return sound

    def pause_sound(self, sound):
        sound.pause()

    def stop_sound(self, sound):
        sound.stop()

    def is_sound_playing(self, sound):
        return True
