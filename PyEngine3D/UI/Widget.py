

class Widget:
    def __init__(self, **kwargs):
        self.__x = 0
        self.__y = 0
        self.__width = 100
        self.__height = 100

        self.parent_widget = None
        self.child_widgets = []

        if 'x' in kwargs:
            self.x = kwargs['x']

        if 'y' in kwargs:
            self.y = kwargs['y']

        self.pos = kwargs.get('pos', [0, 0])

        self.center = kwargs.get('center', [0, 0])
        self.width = kwargs.get('width', 100)
        self.height = kwargs.get('height', 100)
        self.pos_hint_x = kwargs.get('pos_hint_x', 0.0)
        self.pos_hint_y = kwargs.get('pos_hint_y', 0.0)
        self.size_hint_x = kwargs.get('size_hint_x', 1.0)
        self.size_hint_y = kwargs.get('size_hint_y', 1.0)

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, x):
        self.__x = x
