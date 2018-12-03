import numpy as np
import pyglet

from PyEngine3D.Common import *
from PyEngine3D.App.CoreManager import CoreManager


class Widget:
    def __init__(self, **kwargs):
        self.root = kwargs.get('root')
        self.changed_layout = False
        self.parent = None
        self.widgets = []

        self.__x = 0
        self.__y = 0
        self.__width = 100
        self.__height = 100
        self.__pos_hint_x = None
        self.__pos_hint_y = None
        self.__size_hint_x = None
        self.__size_hint_y = None
        self.__color = np.array(kwargs.get('color', [0.0, 0.0, 0.0, 0.0]), np.float32)
        self.__pressed_color = np.array(kwargs.get('pressed_color', [0.0, 0.0, 0.0, 0.0]), np.float32)

        self.name = kwargs.get('name', '')
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.world_x = 0
        self.world_y = 0
        self.width = kwargs.get('width', 100)
        self.height = kwargs.get('height', 100)
        self.pos_hint_x = kwargs.get('pos_hint_x', None)
        self.pos_hint_y = kwargs.get('pos_hint_y', None)
        self.size_hint_x = kwargs.get('size_hint_x', None)
        self.size_hint_y = kwargs.get('size_hint_y', None)
        self.touch_offset_x = 0
        self.touch_offset_y = 0

        self.dragable = kwargs.get('dragable', False)
        self.touchable = kwargs.get('touchable', False) or self.dragable
        self.touched = False
        self.pressed = False

        self.text = kwargs.get('text', '')
        self.font_size = 10
        self.text_render_queue = None

        self.texture = kwargs.get('texture')

    def set_text(self, text, font_size=10):
        core_manager = CoreManager.instance()
        self.text = text
        self.font_size = font_size
        self.text_render_queue = core_manager.font_manager.compile_text(text, font_size=font_size)

    def collide(self, x, y):
        return self.world_x <= x < (self.world_x + self.width) and self.world_y <= y < (self.world_y + self.height)

    def on_touch_down(self, x, y):
        self.touched = True
        if self.dragable:
            self.touch_offset_x = self.x - x
            self.touch_offset_y = self.y - y

    def on_touch_move(self, x, y):
        if self.touched:
            if self.dragable:
                self.x = x + self.touch_offset_x
                self.y = y + self.touch_offset_y

    def on_touch_up(self, x, y):
        if self.touched:
            self.touched = False
            if self.dragable:
                self.x = x + self.touch_offset_x
                self.y = y + self.touch_offset_y

    @property
    def color(self):
        return self.__color

    @color.setter
    def color(self, color):
        self.__color[...] = color

    @property
    def opacity(self):
        return self.__color[3]

    @opacity.setter
    def opacity(self, opacity):
        self.__color[3] = opacity

    @property
    def pressed_color(self):
        return self.__pressed_color

    @pressed_color.setter
    def pressed_color(self, color):
        self.__pressed_color[...] = color

    @property
    def pressed_opacity(self):
        return self.__pressed_color[3]

    @pressed_opacity.setter
    def pressed_opacity(self, opacity):
        self.__pressed_color[3] = opacity

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, x):
        if self.__x != x:
            self.changed_layout = True
            self.__pos_hint_x = None
            self.__x = x

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, y):
        if self.__y != y:
            self.changed_layout = True
            self.__pos_hint_y = None
            self.__y = y

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, width):
        if self.__width != width:
            self.changed_layout = True
            self.__size_hint_x = None
            self.__width = width

    @property
    def height(self):
        return self.__height

    @height.setter
    def height(self, height):
        if self.__height != height:
            self.changed_layout = True
            self.__size_hint_y = None
            self.__height = height

    @property
    def pos_hint_x(self):
        return self.__pos_hint_x

    @pos_hint_x.setter
    def pos_hint_x(self, pos_hint_x):
        if pos_hint_x is not None and self.__pos_hint_x != pos_hint_x:
            self.changed_layout = True
            self.__pos_hint_x = pos_hint_x

    @property
    def pos_hint_y(self):
        return self.__pos_hint_y

    @pos_hint_y.setter
    def pos_hint_y(self, pos_hint_y):
        if pos_hint_y is not None and self.__pos_hint_y != pos_hint_y:
            self.changed_layout = True
            self.__pos_hint_y = pos_hint_y

    @property
    def size_hint_x(self):
        return self.__size_hint_x

    @size_hint_x.setter
    def size_hint_x(self, size_hint_x):
        if size_hint_x is not None and self.__size_hint_x != size_hint_x:
            self.changed_layout = True
            self.__size_hint_x = size_hint_x

    @property
    def size_hint_y(self):
        return self.__size_hint_y

    @size_hint_y.setter
    def size_hint_y(self, size_hint_y):
        if size_hint_y is not None and self.__size_hint_y != size_hint_y:
            self.changed_layout = True
            self.__size_hint_y = size_hint_y

    def update_layout(self, changed_layout=False):
        changed_layout = self.changed_layout or changed_layout

        if changed_layout:
            if self.parent is not None:
                if self.pos_hint_x is not None:
                    self.x = self.pos_hint_x * self.parent.width

                if self.pos_hint_y is not None:
                    self.y = self.pos_hint_y * self.parent.height

                if self.size_hint_x is not None:
                    self.width = self.size_hint_x * self.parent.width

                if self.size_hint_y is not None:
                    self.height = self.size_hint_y * self.parent.height

            self.world_x = self.x
            self.world_y = self.y

            if self.parent is not None:
                self.world_x += self.parent.world_x
                self.world_y += self.parent.world_y

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
        if widget not in self.widgets:
            widget.parent = self
            widget.root = self if self.root is None else self.root
            widget.update_layout(self.changed_layout)
            self.widgets.append(widget)

    def remove_widget(self, widget):
        if widget in self.widgets:
            self.widgets.remove(widget)

    def update(self, dt, game_backend, touch_event=False):
        for widget in self.widgets:
            touch_event = widget.update(dt, game_backend, touch_event)

        if not touch_event and self.touchable:
            click_left, click_middle, click_right = game_backend.get_mouse_clicked()
            pressed_left, pressed_middle, pressed_right = game_backend.get_mouse_pressed()
            mouse_x, mouse_y = game_backend.mouse_pos[0], game_backend.mouse_pos[1]

            if self.touched:
                if pressed_left:
                    self.on_touch_move(mouse_x, mouse_y)
                else:
                    self.on_touch_up(mouse_x, mouse_y)
            elif click_left and self.collide(mouse_x, mouse_y):
                self.on_touch_down(mouse_x, mouse_y)

        return self.touched or touch_event

    def render(self, material_instance, mesh):
        if 0.0 <= self.opacity:
            if self.pressed:
                material_instance.bind_uniform_data("color", self.pressed_color)
            else:
                material_instance.bind_uniform_data("color", self.color)

            material_instance.bind_uniform_data("pos_size", [self.world_x, self.world_y, self.width, self.height])

            if self.texture is not None:
                material_instance.bind_uniform_data("texture_diffuse", self.texture)
                material_instance.bind_uniform_data("is_render_diffuse", True)
            else:
                material_instance.bind_uniform_data("is_render_diffuse", False)

            mesh.draw_elements()

        if self.text:
            core_manager = CoreManager.instance()
            core_manager.font_manager.render_font(self.root.width, self.root.height, self.font_size, self.text_render_queue)

        for widget in self.widgets:
            widget.render(material_instance=material_instance, mesh=mesh)


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
