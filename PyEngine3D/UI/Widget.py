
class Widget:
    def __init__(self, name='', x=0, y=0, width=100, height=100, rendertarget=None):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rendertarget = rendertarget
        self.widgets = []

    def resize(self, width, height):
        self.width = int(width)
        self.height = int(height)

    def bind_rendertarget(self, rendertarget):
        self.rendertarget = rendertarget

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
        if self.rendertarget is not None:
            material_instance.bind_uniform_data("texture_diffuse", self.rendertarget)
            material_instance.bind_uniform_data("is_render_diffuse", True)
        else:
            material_instance.bind_uniform_data("is_render_diffuse", False)

        mesh.draw_elements()

        for widget in self.widgets:
            widget.render(material_instance=material_instance, mesh=mesh)
