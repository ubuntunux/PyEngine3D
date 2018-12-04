from OpenGL.GL import *

from PyEngine3D.Common import *
from PyEngine3D.Utilities import *
from PyEngine3D.OpenGLContext import FrameBufferManager
from PyEngine3D.Render import ScreenQuad, RenderTargets
from .Widget import Widget, Button


class ViewportManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.resource_manager = None
        self.renderer = None
        self.framebuffer_manager = None
        self.root = None
        self.main_viewport = None
        self.touch_event = False

        self.quad = None
        self.render_widget = None

    def initialize(self, core_manager):
        self.touch_event = False
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.renderer = core_manager.renderer
        self.framebuffer_manager = FrameBufferManager.instance()

        self.quad = ScreenQuad.get_vertex_array_buffer()
        self.render_widget = self.resource_manager.get_material_instance('ui.render_widget')

        width, height = self.core_manager.get_window_size()

        self.root = Widget(name="root", width=width, height=height)
        self.main_viewport = Widget(name="Main viewport", size_hint_x=0.5, size_hint_y=0.5)
        self.root.add_widget(self.main_viewport)

    def build_ui(self):
        side_viewport = Button(name="Side viewport", dragable=True, size_hint_x=0.5, size_hint_y=0.5)
        btn = Button(name="Side viewport", x=100, y=100, width=100, height=100)
        btn.set_text("test dqwdwq", font_size=8)
        side_viewport.add_widget(btn)

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
        self.touch_event = self.root.update(dt, touch_event=False)
        self.root.update_layout()
        return self.touch_event

    def render(self):
        self.renderer.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.framebuffer_manager.bind_framebuffer(RenderTargets.SCREENBUFFER)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        self.render_widget.use_program()
        self.render_widget.bind_material_instance()

        self.root.render(material_instance=self.render_widget, mesh=self.quad)

        # blit frame buffer
        self.framebuffer_manager.blit_framebuffer()
        self.framebuffer_manager.unbind_framebuffer()
