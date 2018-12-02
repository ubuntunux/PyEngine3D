from PyEngine3D.Common import *


class Widget:
    def __init__(self, name='', **kwargs):
        self.name = name
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.width = kwargs.get('width', 100)
        self.height = kwargs.get('height', 100)
        self.color = kwargs.get('color')
        self.texture = kwargs.get('texture')
        self.widgets = []

    def resize(self, width, height):
        self.width = int(width)
        self.height = int(height)

    def bind_texture(self, texture):
        self.texture = texture

    def clear_widgets(self):
        for widget in self.widgets:
            widget.clear_widgets()

        self.widgets = []

    def add_widget(self, widget):
        if widget not in self.widgets:
            self.widgets.append(widget)

    def remove_widget(self, widget):
        if widget in self.widgets:
            self.widgets.remove(widget)

    def update(self, dt):
        for widget in self.widgets:
            widget.update(dt)

    def render(self, material_instance, mesh):
        if self.texture is not None:
            material_instance.bind_uniform_data("texture_diffuse", self.texture)
            material_instance.bind_uniform_data("is_render_diffuse", True)
        else:
            material_instance.bind_uniform_data("is_render_diffuse", False)

        mesh.draw_elements()

        for widget in self.widgets:
            widget.render(material_instance=material_instance, mesh=mesh)
