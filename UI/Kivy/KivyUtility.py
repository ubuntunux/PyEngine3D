import time

from UI import logger
from Utilities import Singleton

# ---------------------#
# Kivy
# ---------------------#
import kivy
from kivy.app import App

from kivy.config import Config
Config.set('graphics', 'resizable', '1')
Config.set('graphics', 'width', '920')
Config.set('graphics', 'height', '800')


# ---------------------#
# Utilities
# ---------------------#
pos_hint_center = {'center_x':0.5, 'center_y':0.5}


def add(A, B):
    if type(B) != tuple and type(B) != list:
        return [i + B for i in A]
    else:
        return [A[i] + B[i] for i in range(len(A))]


def sub(A, B):
    if type(B) != tuple and type(B) != list:
        return [i - B for i in A]
    else:
        return [A[i] - B[i] for i in range(len(A))]


def mul(A, B):
    if type(B) != tuple and type(B) != list:
        return [i * B for i in A]
    else:
        return [A[i] * B[i] for i in range(len(A))]


def div(A, B):
    if type(B) != tuple and type(B) != list:
        return [i / B for i in A]
    else:
        return [A[i] / B[i] for i in range(len(A))]


def dot(A, B):
    return sum(mul(A, B))


def getDist(A, B=None):
    temp = sub(A, B) if B else A
    return sqrt(sum([i * i for i in temp]))


def normalize(A, dist=None):
    if dist is None:
        dist = getDist(A)
    return div(A, dist) if dist > 0.0 else mul(A, 0.0)


# ---------------------#
# CLASS : MyRoot
# ---------------------#
class MyApp(App, Singleton):
    def __init__(self):
        super(MyApp, self).__init__()
        self.validExit = False
        self.buildDone = False
        self.bButtonLock = False

        self.bPopup = False
        self.popupLayout = None

        self.bProgress = False
        self.progressPopup = None
        self.progress = None
        self.progressTitle = ""
        self.progressCount = 0

        self.appList = []
        self.appInitializeList = []
        self.appUpdateList = []
        self.appUpdateStateList = []
        self.app = None

        self.W = 0.0
        self.H = 0.0
        self.WW = 0.0
        self.HH = 0.0
        self.WH = 0.0
        self.WRatio = 0.0
        self.HRatio = 0.0
        self.cX = 0.0
        self.cY = 0.0
        self.cXY = (0.0, 0.0)

        self.screenMgr = None
        self.transition = None
        self.emptyScreen = None
        self.root_widget = None
        self.onTouchPrev = None
        self._keyboard = None
        self.y = 0
        self.x = 0

    def to_window(self, *args):
        return 0, 0

    def load_modules(self):
        from kivy import metrics
        from kivy.animation import Animation
        from kivy.clock import Clock
        from kivy.config import Config
        from kivy.core.window import Window
        from kivy.core.audio import SoundLoader
        from kivy.extras.highlight import KivyLexer
        from kivy.factory import Factory
        from kivy.graphics import Color, Rectangle, Point, GraphicException, Line, Quad, Ellipse, Fbo, RenderContext
        from kivy.graphics.instructions import Instruction
        from kivy.graphics.opengl import glLineWidth
        from kivy.logger import Logger
        from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
        from kivy.uix.accordion import Accordion, AccordionItem
        from kivy.uix.anchorlayout import AnchorLayout
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.codeinput import CodeInput
        from kivy.uix.dropdown import DropDown
        from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
        from kivy.uix.floatlayout import FloatLayout
        from kivy.uix.gridlayout import GridLayout
        from kivy.uix.image import Image
        from kivy.uix.label import Label
        from kivy.uix.modalview import ModalView
        from kivy.uix.popup import Popup
        from kivy.uix.progressbar import ProgressBar
        from kivy.uix.relativelayout import RelativeLayout
        from kivy.uix.scatter import Scatter
        from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, SwapTransition, WipeTransition, \
            FadeTransition
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.slider import Slider
        from kivy.uix.spinner import Spinner
        from kivy.uix.stacklayout import StackLayout
        from kivy.uix.textinput import TextInput
        from kivy.uix.togglebutton import ToggleButton
        from kivy.uix.treeview import TreeView, TreeViewLabel
        from kivy.uix.widget import Widget
        from kivy.vector import Vector

        modules = locals()
        for moduleName in modules:
            setattr(self, moduleName, modules[moduleName])

    def build(self):
        self.load_modules()

        self.W = float(self.Window.size[0])
        self.H = float(self.Window.size[1])
        self.WW = (self.W, self.W)
        self.HH = (self.H, self.H)
        self.WH = (self.W, self.H)
        self.WRatio = self.H / self.W
        self.HRatio = self.W / self.H
        self.cX = self.W * 0.5
        self.cY = self.H * 0.5
        self.cXY = (self.W * 0.5, self.H * 0.5)

        self.root = self.FloatLayout(size_hint=(1, 1), pos_hint={'center_x':0.5, 'center_y':0.5})
        self.root_widget = self.FloatLayout(size_hint=(1, 1), pos_hint={'center_x':0.5, 'center_y':0.5})

        self.screenMgr = self.ScreenManager(size_hint=(1, 1), pos_hint={'center_x':0.5, 'center_y':0.5})
        self.transition = self.WipeTransition()
        # or self.transition = self.SlideTransition(direction="down")
        self.emptyScreen = self.Screen(name="empty screen")
        # self.emptyScreen.add_widget(self.Label(text="empty.screen"))
        self.add_screen(self.emptyScreen)
        self.current_screen(self.emptyScreen)

        self.bButtonLock = False
        self.bPopup = False

        self.root.add_widget(self.screenMgr)
        self.root.add_widget(self.root_widget)

        self.bind(on_start=self.post_build_init)
        self.onTouchPrev = self.popup_exit
        self.buildDone = True
        return self.root

    def post_build_init(self, ev):
        self._keyboard = self.Window.request_keyboard(self._keyboard_closed, self, 'text')
        if self._keyboard.widget:
            # If it exists, this widget is a VKeyboard object which you can use to change the keyboard layout.
            pass
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        # regist update function
        time.sleep(1.0)
        self.Clock.schedule_interval(self.update, 0)

    def _keyboard_closed(self):
        # print('My keyboard have been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'escape':
            if self.bPopup and self.popupLayout:
                self.popupLayout.dismiss()
                self.bPopup = False
            else:
                self.onTouchPrev()
        # Return True to accept the key. Otherwise, it will be used by the system.
        return True

    def regist(self, app):
        if app:
            if app in self.appList:
                return

            # initialize
            if hasattr(app, "initialize"):
                self.appInitializeList.append(app)
            else:
                raise AttributeError("App must be implemented initialize function..")

            # update method
            if hasattr(app, "update"):
                self.appUpdateList.append(app)
            else:
                raise AttributeError("App must be implemented update function..")

            # update state
            if hasattr(app, "updateState"):
                self.appUpdateStateList.append(app)

            # regist app
            self.appList.append(app)

    def remove(self, app):
        if app in self.appList:
            self.appList.remove(app)
        if app in self.appUpdateList:
            self.appUpdateList.remove(app)
        if app in self.appUpdateStateList:
            self.appUpdateStateList.remove(app)
        if app in self.appInitializeList:
            self.appInitializeList.remove(app)

    def update(self, frameTime):
        if not self.buildDone:
            return

        if self.appInitializeList:
            for app in self.appInitializeList:
                app.initialize()
            self.appInitializeList = []

        for app in self.appUpdateList:
            app.update(frameTime)

        for app in self.appUpdateStateList:
            app.updateState(frameTime)

    def run(self, title, app=None):
        self.title = title
        self.app = app
        self.regist(app)
        App.run(self)

    def exit(self, *args):
        self.validExit = True
        self._keyboard.release()
        self.stop()

    def on_pause(self):
        return True

    # ------------------ #
    # Widget
    # ------------------ #
    def add_widget(self, widget):
        self.root_widget.add_widget(widget)

    def remove_widget(self, widget):
        self.root_widget.remove_widget(widget)

    # ------------------- #
    # Screen
    # ------------------- #
    def prev_screen(self):
        prev_screen = self.screenMgr.previous()
        if prev_screen:
            self.screenMgr.current = prev_screen

    def add_screen(self, screen):
        if screen.name not in self.screenMgr.screen_names:
            self.screenMgr.add_widget(screen)

    def current_screen(self, screen):
        if self.screenMgr.current != screen.name:
            if not self.screenMgr.has_screen(screen.name):
                self.add_screen(screen)
            self.screenMgr.current = screen.name

    def remove_screen(self, screen):
        if screen.name in self.screenMgr.screen_names:
            self.screenMgr.remove_widget(screen)
            self.prev_screen()

    def get_current_screen(self):
        return self.screenMgr.current_screen

    # ------------------ #
    # TouchPrev
    # ------------------ #
    def getTouchPrev(self):
        return self.onTouchPrev

    def setTouchPrev(self, func):
        self.onTouchPrev = func if func else self.popup_exit

    # ------------------ #
    # Popup
    # ------------------ #
    def popup_exit(self):
        self.popup("Exit?", "", self.exit, None)

    def popup(self, title, message, lambdaYes, lambdaNo):
        if self.bPopup:
            return
        self.bPopup = True
        content = self.BoxLayout(orientation="vertical", size_hint=(1, 1))
        self.popupLayout = self.Popup(title=title, content=content, auto_dismiss=False, size_hint=(0.9, 0.3))
        content.add_widget(self.Label(text=message))
        btnLayout = self.BoxLayout(orientation="horizontal", size_hint=(1, 1), spacing=kivy.metrics.dp(20))
        btn_Yes = self.Button(text='Yes')
        btn_No = self.Button(text='No')
        btnLayout.add_widget(btn_No)
        btnLayout.add_widget(btn_Yes)
        content.add_widget(btnLayout)

        def closePopup(instance, bYes):
            if bYes and lambdaYes:
                lambdaYes()
            elif lambdaNo:
                lambdaNo()
            self.popupLayout.dismiss()
            self.bPopup = False

        btn_Yes.bind(on_press=lambda inst: closePopup(inst, True))
        btn_No.bind(on_press=lambda inst: closePopup(inst, False))
        self.popupLayout.open()
        return

    # ------------------ #
    # Progress
    # ------------------ #
    def isProgress(self):
        return self.bProgress

    def createProgressPopup(self, title, itemCount):
        self.destroyProgressPopup()
        # loading flag
        self.bProgress = True
        content = self.Widget()
        sizehintW = 0.3
        sizehintH = 0.25
        self.progressTitle = title
        self.progressCount = itemCount
        title = "%s : 0 / %d" % (title, itemCount)
        self.progressPopup = self.Popup(title=title, content=content, auto_dismiss=False, size_hint=(sizehintW, sizehintH))
        content.pos = self.progressPopup.pos
        pbSize = mul(self.WH, (sizehintW * 0.9, sizehintH * 0.9))
        self.progress = self.ProgressBar(value=0, max=itemCount,
                                         pos=sub(self.cXY, (pbSize[0] * 0.5, sizehintH * self.H * 0.5)), size=pbSize)
        content.add_widget(self.progress)
        self.progressPopup.open()

    def increaseProgress(self):
        if self.progress:
            self.progress.value += 1
            title = "%s : %d / %d" % (self.progressTitle, self.progress.value, self.progressCount)
            self.progressPopup.title = title

    def destroyProgressPopup(self):
        if self.progressPopup:
            self.progressPopup.dismiss()
            self.progressPopup = None
        # loading flag
        self.bProgress = False
