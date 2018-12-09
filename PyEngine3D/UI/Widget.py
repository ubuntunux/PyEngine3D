import numpy as np
import pyglet

from PyEngine3D.Common import *
from PyEngine3D.Render import TextRenderData


class Widget:
    core_manager = None
    viewport_manager = None
    root = None
    haligns = ('left', 'center', 'right')
    valigns = ('top', 'center', 'bottom')

    def __init__(self, **kwargs):
        self.changed_layout = False
        self.parent = None
        self.widgets = []

        self._x = 0.0
        self._y = 0.0
        self._width = 100.0
        self._height = 100.0
        self._halign = ''
        self._valign = ''
        self._pos_hint_x = None
        self._pos_hint_y = None
        self._size_hint_x = None
        self._size_hint_y = None
        self._color = np.array(kwargs.get('color', [0.0, 0.0, 0.0, 0.0]), np.float32)
        self._pressed_color = np.array(kwargs.get('pressed_color', [0.0, 0.0, 0.0, 0.0]), np.float32)

        self.name = kwargs.get('name', '')
        self.x = kwargs.get('x', 0.0)
        self.y = kwargs.get('y', 0.0)
        self.width = kwargs.get('width', 100.0)
        self.height = kwargs.get('height', 100.0)
        self.halign = kwargs.get('halign', '')  # ('left', 'center', 'right')
        self.valign = kwargs.get('valign', '')  # ('top', 'center', 'bottom')
        self.pos_hint_x = kwargs.get('pos_hint_x')
        self.pos_hint_y = kwargs.get('pos_hint_y')
        self.size_hint_x = kwargs.get('size_hint_x')
        self.size_hint_y = kwargs.get('size_hint_y')
        self.texcoord = np.array(kwargs.get('texcoord', [0.0, 0.0, 1.0, 1.0]), np.float32)
        self.dragable = kwargs.get('dragable', False)
        self.touchable = kwargs.get('touchable', False) or self.dragable
        self.texture = kwargs.get('texture')

        self.center_x = 0.0
        self.center_y = 0.0
        self.world_x = 0.0
        self.world_y = 0.0
        self.world_center_x = 0.0
        self.world_center_y = 0.0
        self.touch_offset_x = 0.0
        self.touch_offset_y = 0.0

        self.touched = False
        self.pressed = False

        self.callback_touch_down = None
        self.callback_touch_move = None
        self.callback_touch_up = None

        self.text_widget = None
        text = kwargs.get('text', '')
        font_size = kwargs.get('font_size', 10)

        if text:
            self.set_text(self.text, font_size)

    def set_text(self, text, font_size=10):
        # create text widget
        if self.text_widget is None:
            self.text_widget = Text(halign='center', valign='center')
            self.add_widget(self.text_widget)
        self.text_widget.set_text(text, font_size)

    def collide(self, x, y):
        return self.world_x <= x < (self.world_x + self.width) and self.world_y <= y < (self.world_y + self.height)

    def bind(self, **kwargs):
        for key in kwargs:
            if self.on_touch_down.__name__ == key:
                self.callback_touch_down = kwargs[key]
            elif self.on_touch_move.__name__ == key:
                self.callback_touch_move = kwargs[key]
            elif self.on_touch_up.__name__ == key:
                self.callback_touch_up = kwargs[key]

    def on_touch_down(self, x, y):
        self.touched = True
        if self.dragable:
            self.touch_offset_x = self.x - x
            self.touch_offset_y = self.y - y

            if self.callback_touch_down is not None:
                self.callback_touch_down(self, x, y)

    def on_touch_move(self, x, y):
        if self.touched:
            if self.dragable:
                self.x = x + self.touch_offset_x
                self.y = y + self.touch_offset_y

                if self.callback_touch_move is not None:
                    self.callback_touch_move(self, x, y)

    def on_touch_up(self, x, y):
        if self.touched:
            self.touched = False
            if self.dragable:
                self.x = x + self.touch_offset_x
                self.y = y + self.touch_offset_y

                if self.callback_touch_up is not None:
                    self.callback_touch_up(self, x, y)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color[...] = color

    @property
    def opacity(self):
        return self._color[3]

    @opacity.setter
    def opacity(self, opacity):
        self._color[3] = opacity

    @property
    def pressed_color(self):
        return self._pressed_color

    @pressed_color.setter
    def pressed_color(self, color):
        self._pressed_color[...] = color

    @property
    def pressed_opacity(self):
        return self._pressed_color[3]

    @pressed_opacity.setter
    def pressed_opacity(self, opacity):
        self._pressed_color[3] = opacity

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        if self._x != x:
            self.changed_layout = True
            self.pos_hint_x = None
            self._x = x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        if self._y != y:
            self.changed_layout = True
            self.pos_hint_y = None
            self._y = y

    @property
    def halign(self):
        return self._halign

    @halign.setter
    def halign(self, halign):
        if halign in self.haligns and halign != self._halign:
            self.changed_layout = True
            self.pos_hint_x = None
            self._halign = halign

    @property
    def valign(self):
        return self._valign

    @valign.setter
    def valign(self, valign):
        if valign in self.valigns and valign != self._valign:
            self.changed_layout = True
            self.pos_hint_y = None
            self._valign = valign

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width):
        if self._width != width:
            self.changed_layout = True
            self.size_hint_x = None
            self._width = width

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height):
        if self._height != height:
            self.changed_layout = True
            self.size_hint_y = None
            self._height = height

    @property
    def pos_hint_x(self):
        return self._pos_hint_x

    @pos_hint_x.setter
    def pos_hint_x(self, pos_hint_x):
        if pos_hint_x is not None and self._pos_hint_x != pos_hint_x:
            self.changed_layout = True
        self._pos_hint_x = pos_hint_x

    @property
    def pos_hint_y(self):
        return self._pos_hint_y

    @pos_hint_y.setter
    def pos_hint_y(self, pos_hint_y):
        if pos_hint_y is not None and self._pos_hint_y != pos_hint_y:
            self.changed_layout = True
        self._pos_hint_y = pos_hint_y

    @property
    def size_hint_x(self):
        return self._size_hint_x

    @size_hint_x.setter
    def size_hint_x(self, size_hint_x):
        if size_hint_x is not None and self._size_hint_x != size_hint_x:
            self.changed_layout = True
        self._size_hint_x = size_hint_x

    @property
    def size_hint_y(self):
        return self._size_hint_y

    @size_hint_y.setter
    def size_hint_y(self, size_hint_y):
        if size_hint_y is not None and self._size_hint_y != size_hint_y:
            self.changed_layout = True
        self._size_hint_y = size_hint_y

    def update_layout(self, changed_layout=False):
        changed_layout = self.changed_layout or changed_layout

        if changed_layout:
            if self.parent is not None:
                # NOTE : If you set the value to x instead of __x, the value of __size_hint_x will be none by @__x.setter.
                if self._halign:
                    if 'left' == self._halign:
                        self._x = 0
                    elif 'right' == self._halign:
                        self._x = self.parent.width - self._width
                    else:
                        self._x = (self.parent.width - self._width) * 0.5
                elif self._pos_hint_x is not None:
                    self._x = self._pos_hint_x * self.parent.width

                if self._valign:
                    if 'bottom' == self._valign:
                        self._y = 0
                    elif 'top' == self._valign:
                        self._y = self.parent.height - self._height
                    else:
                        self._y = (self.parent.height - self._height) * 0.5
                elif self._pos_hint_y is not None:
                    self._y = self._pos_hint_y * self.parent.height

                if self._size_hint_x is not None:
                    self._width = self._size_hint_x * self.parent.width

                if self._size_hint_y is not None:
                    self._height = self._size_hint_y * self.parent.height

            self.center_x = self._x + self._width / 2
            self.center_y = self._y + self._height / 2
            self.world_x = self._x
            self.world_y = self._y

            if self.parent is not None:
                self.world_x += self.parent.world_x
                self.world_y += self.parent.world_y
                self.world_center_x = self.center_x + self.parent.world_x
                self.world_center_y = self.center_y + self.parent.world_y

            self.changed_layout = False

        for widget in self.widgets:
            widget.update_layout(changed_layout)

    def bind_texture(self, texture):
        self.texture = texture

    def clear_widgets(self):
        for widget in self.widgets:
            widget.clear_widgets()

        self.widgets = []

    def add_widget(self, widget):
        if widget.parent is not None:
            raise AttributeError("Widget already has parent.")

        if widget not in self.widgets:
            widget.parent = self
            widget.update_layout(self.changed_layout)
            self.widgets.append(widget)

    def remove_widget(self, widget):
        if widget in self.widgets:
            widget.parent = None
            self.widgets.remove(widget)

    def update(self, dt, touch_event=False):
        for widget in self.widgets:
            touch_event = widget.update(dt, touch_event)

        if not touch_event and self.touchable:
            click_left, click_middle, click_right = self.core_manager.get_mouse_clicked()
            pressed_left, pressed_middle, pressed_right = self.core_manager.get_mouse_pressed()
            mouse_x, mouse_y = self.core_manager.get_mouse_pos()

            if self.touched:
                if pressed_left:
                    self.on_touch_move(mouse_x, mouse_y)
                else:
                    self.on_touch_up(mouse_x, mouse_y)
            elif click_left and self.collide(mouse_x, mouse_y):
                self.on_touch_down(mouse_x, mouse_y)

        return self.touched or touch_event

    def render(self, last_program, render_widget_program, mesh):
        if 0.0 <= self.opacity:
            render_widget_program.use_program()
            render_widget_program.bind_material_instance()

            if self.pressed:
                render_widget_program.bind_uniform_data("color", self.pressed_color)
            else:
                render_widget_program.bind_uniform_data("color", self.color)

            render_widget_program.bind_uniform_data("pos_size", [self.world_x, self.world_y, self.width, self.height])
            render_widget_program.bind_uniform_data("texcoord", self.texcoord)

            if self.texture is not None:
                render_widget_program.bind_uniform_data("texture_diffuse", self.texture)
                render_widget_program.bind_uniform_data("is_render_diffuse", True)
            else:
                render_widget_program.bind_uniform_data("is_render_diffuse", False)

            mesh.draw_elements()

        if isinstance(self, Text) and self.text_render_data is not None:
            self.core_manager.renderer.render_text(self.text_render_data,
                                                   self.world_x,
                                                   self.world_y,
                                                   self.root.width,
                                                   self.root.height)

        for widget in self.widgets:
            widget.render(last_program, render_widget_program, mesh)


class Button(Widget):
    def __init__(self, **kwargs):
        super(Button, self).__init__(touchable=True, **kwargs)

        self.pressed = False
        self.color = kwargs.get('color', [0.25, 0.25, 0.25, 1.0])
        self.pressed_color = np.array(kwargs.get('pressed_color', [0.5, 0.5, 1.0, 1.0]), np.float32)

    def on_touch_down(self, x, y):
        super(Button, self).on_touch_down(x, y)
        self.pressed = True

    def on_touch_move(self, x, y):
        super(Button, self).on_touch_move(x, y)

    def on_touch_up(self, x, y):
        super(Button, self).on_touch_up(x, y)
        self.pressed = False


class ToggleButton(Widget):
    def __init__(self, **kwargs):
        super(Button, self).__init__(touchable=True, **kwargs)

        self.pressed = False
        self.color = kwargs.get('color', [0.25, 0.25, 0.25, 1.0])
        self.pressed_color = np.array(kwargs.get('pressed_color', [0.5, 0.5, 1.0, 1.0]), np.float32)

    def on_touch_down(self, x, y):
        super(ToggleButton, self).on_touch_down(x, y)
        self.pressed = not self.pressed


class Text(Widget):
    def __init__(self, **kwargs):
        if 'halign' not in kwargs:
            kwargs['halign'] = 'left'

        if 'valign' not in kwargs:
            kwargs['valign'] = 'bottom'

        super(Text, self).__init__(**kwargs)

        self.text = kwargs.get('text', '')
        self.text_render_data = TextRenderData()

        if self.text:
            self.set_text(self.text)

    def set_text(self, text, font_size=10):
        self.text = text
        font_data = self.core_manager.resource_manager.get_default_font_data()
        changed_layout = self.text_render_data.set_text(text, font_data, font_size=font_size)
        self.update_layout(changed_layout)

    def update_layout(self, changed_layout=False):
        changed_layout = self.changed_layout or changed_layout

        if changed_layout:
            self._width = self.text_render_data.width
            self._height = self.text_render_data.height

            super(Text, self).update_layout(changed_layout)

    @Widget.width.setter
    def width(self, width):
        pass

    @Widget.height.setter
    def height(self, height):
        pass

    @Widget.size_hint_x.setter
    def size_hint_x(self, size_hint_x):
        pass

    @Widget.size_hint_y.setter
    def size_hint_y(self, size_hint_y):
        pass
