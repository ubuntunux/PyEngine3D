
class Widget:
    def __init__(self, name='', x=0, y=0, width=100, height=100):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.widgets = []

    def resize(self, width, height):
        self.width = width
        self.height = height

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

    def render(self):
        for widget in self.widgets:
            widget.render()
