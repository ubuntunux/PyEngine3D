from OpenGL.GL import *

from PyEngine3D.Common import *
from PyEngine3D.Utilities import *
from PyEngine3D.OpenGLContext import FrameBufferManager
from PyEngine3D.Render import ScreenQuad
from .Widget import Widget


class ViewportManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.game_backend = None
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
        self.game_backend = core_manager.game_backend
        self.resource_manager = core_manager.resource_manager
        self.renderer = core_manager.renderer
        self.framebuffer_manager = FrameBufferManager.instance()

        self.quad = ScreenQuad.get_vertex_array_buffer()
        self.render_widget = self.resource_manager.get_material_instance('ui.render_widget')

        self.root = Widget(name="root", width=self.game_backend.width, height=self.game_backend.height)

        self.main_viewport = Widget(name="Main viewport", touchable=True, size_hint_x=0.5, size_hint_y=0.5)
        side_viewport = Widget(name="Side viewport", touchable=True, color=[0.0, 1.0, 0.0, 0.5], size_hint_x=0.5, size_hint_y=0.5)

        self.root.add_widget(self.main_viewport)
        self.root.add_widget(side_viewport)

    def get_window_width(self):
        return self.game_backend.width

    def get_window_height(self):
        return self.game_backend.height

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
        self.touch_event = self.root.update(dt, self.game_backend, touch_event=False)
        self.root.update_layout()
        return self.touch_event

    def render(self):
        self.renderer.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glViewport(0, 0, self.game_backend.width, self.game_backend.height)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT)

        self.render_widget.use_program()
        self.render_widget.bind_material_instance()

        self.root.render(material_instance=self.render_widget, mesh=self.quad)

        # blit frame buffer
        # self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        # self.framebuffer_manager.blit_framebuffer(dst_w=self.main_viewport.width, dst_h=self.main_viewport.height)
        # self.framebuffer_manager.unbind_framebuffer()
