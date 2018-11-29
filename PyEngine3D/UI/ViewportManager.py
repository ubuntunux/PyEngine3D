from PyEngine3D.Utilities import *
from PyEngine3D.OpenGLContext import FrameBufferManager
from PyEngine3D.Render import RenderTargets
from .Widget import Widget


class ViewportManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.renderer = None
        self.framebuffer_manager = None
        self.main_viewport = None

        self.widgets = []

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.renderer = core_manager.renderer
        self.framebuffer_manager = FrameBufferManager.instance()

        self.main_viewport = Widget(name="Main viewport")
        self.add_widget(self.main_viewport)

    def resize(self, width, height):
        self.main_viewport.resize(width, height)

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
        for widget in self.widgets:
            widget.render()

        # blit frame buffer
        self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        self.framebuffer_manager.blit_framebuffer(dst_w=self.main_viewport.width, dst_h=self.main_viewport.height)
        self.framebuffer_manager.unbind_framebuffer()
