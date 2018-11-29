from OpenGL.GL import *

from PyEngine3D.Utilities import *
from PyEngine3D.OpenGLContext import FrameBufferManager
from PyEngine3D.Render import ScreenQuad
from PyEngine3D.Common import *
from .Widget import Widget


class ViewportManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.renderer = None
        self.framebuffer_manager = None
        self.main_viewport = None
        self.widgets = []

        self.quad = None
        self.render_widget = None

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.game_backend = core_manager.game_backend
        self.resource_manager = core_manager.resource_manager
        self.renderer = core_manager.renderer
        self.framebuffer_manager = FrameBufferManager.instance()

        self.quad = ScreenQuad.get_vertex_array_buffer()
        self.render_widget = self.resource_manager.get_material_instance('ui.render_widget')

        self.main_viewport = Widget(name="Main viewport")
        side_viewport = Widget(name="Side viewport")
        self.add_widget(self.main_viewport)
        self.add_widget(side_viewport)

    def resize_viewport(self, width, height):
        for widget in self.widgets:
            widget.resize(width, height)

    def clear_widgets(self):
        for widget in self.widgets:
            widget.clear_widgets()

        self.widgets = [self.main_viewport, ]

    def add_widget(self, widget):
        if widget not in self.widgets:
            self.widgets.append(widget)

    def remove_widget(self, widget):
        if widget in self.widgets:
            self.widgets.remove(widget)

    def update(self, dt):
        for widget in self.widgets:
            widget.update(dt)

    def render(self):
        self.renderer.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)

        self.render_widget.use_program()
        self.render_widget.bind_material_instance()

        for widget in self.widgets:
            widget.render(material_instance=self.render_widget, mesh=self.quad)

        # blit frame buffer
        # self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        # self.framebuffer_manager.blit_framebuffer(dst_w=self.main_viewport.width, dst_h=self.main_viewport.height)
        # self.framebuffer_manager.unbind_framebuffer()
