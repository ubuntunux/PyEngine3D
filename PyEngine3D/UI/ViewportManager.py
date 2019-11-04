from OpenGL.GL import *

from PyEngine3D.Common import *
from PyEngine3D.App.GameBackend import Keyboard
from PyEngine3D.Utilities import *
from PyEngine3D.OpenGLContext import FrameBufferManager
from PyEngine3D.Render import ScreenQuad, RenderTargets
from .Widget import Align, Orientation
from .Widget import Widget, Button, ToggleButton, Label, TextEdit
from .Widget import BoxLayout


class ViewportManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.resource_manager = None
        self.renderer = None
        self.framebuffer_manager = None
        self.root = None
        self.main_viewport = None
        self.touch_event = False
        self.focused_widget = None

        self.quad = None
        self.render_widget = None

    def initialize(self, core_manager):
        self.touch_event = False
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.renderer = core_manager.renderer
        self.framebuffer_manager = FrameBufferManager.instance()

        if not self.core_manager.is_basic_mode:
            self.quad = ScreenQuad.get_vertex_array_buffer()
            self.render_widget = self.resource_manager.get_material_instance('ui.render_widget')

        width, height = self.core_manager.get_window_size()

        self.root = Widget(name="root", width=width, height=height)
        self.main_viewport = Widget(name="Main viewport", dragable=False, size_hint_x=1.0,  size_hint_y=1.0)
        self.root.add_widget(self.main_viewport)

        # Set static members
        Widget.core_manager = core_manager
        Widget.viewport_manager = self
        Widget.root = self.root

    def build_ui_example(self):
        side_viewport = Button(name="Side viewport", dragable=True, padding_x=10, padding_y=20, size_hint_x=0.5, size_hint_y=0.5, color=[1.0, 1.0, 1.0, 0.1])
        btn = Button(name="Side viewport", text="side_viewport", size_hint_x=1.0, size_hint_y=1.0, color=[1.0, 1.0, 0.0, 0.1])
        btn.set_text("Count", font_size=16)

        text = Label(name="Text", pos_hint_x=1.0, x=100, y=100, width=200, height=200, color=[1.0, 1.0, 1.0, 0.1])
        text.set_text("Count dwqdwqd", font_size=16)
        side_viewport.add_widget(text)
        side_viewport.add_widget(btn)

        layout = BoxLayout(name="BoxLayout", dragable=True, padding_x=80.0, padding_y=40.0, spacing=10, x=0, size_hint_x=1.0, size_hint_y=0.3, color=[1.0, 1.0, 1.0, 0.2], orientation=Orientation.HORIZONTAL)
        btn1 = Button(name="btn1", text="btn1", font_size=16, dragable=True, x=100, width=150, size_hint_y=1.0, color=[1.0, 1.0, 0.0, 0.1])
        btn2 = TextEdit(name="btn2", text="TextEdit", touchable=True, font_size=20, x=200, width=50, size_hint_y=1.0, color=[0.0, 0.0, 1.0, 0.1])
        layout.add_widget(btn1)
        layout.add_widget(btn2)
        self.main_viewport.add_widget(layout)
        btn1.size_hint_x = 10.0
        btn2.size_hint_x = 10.0

        self.main_viewport.add_widget(side_viewport)

    def resize_viewport(self, width, height):
        self.root.width = width
        self.root.height = height
        self.root.update_layout()

    def clear_widgets(self):
        self.root.clear_widgets()

        # reserve main_viewport
        self.root.add_widget(self.main_viewport)

    def add_widget(self, widget):
        self.root.add_widget(widget)

    def remove_widget(self, widget):
        self.root.remove_widget(widget)

    def update(self, dt):
        if self.root is None:
            return False

        self.touch_event = self.root.update(dt, touch_event=False)
        self.root.update_layout()

        if self.focused_widget is not None and isinstance(self.focused_widget, TextEdit):
            if self.core_manager.is_keyboard_pressed():
                if self.core_manager.is_key_pressed(Keyboard.BACKSPACE):
                    if 0 < len(self.focused_widget.text):
                        self.focused_widget.text = self.focused_widget.text[:-1]
                else:
                    text = self.focused_widget.text + self.core_manager.get_text()
                    self.focused_widget.text = text

        return self.touch_event

    def render(self):
        self.renderer.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.framebuffer_manager.bind_framebuffer(RenderTargets.SCREENBUFFER)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        self.root.render(None, self.render_widget, self.quad)

        # blit frame buffer
        self.framebuffer_manager.blit_framebuffer()
        self.framebuffer_manager.unbind_framebuffer()
