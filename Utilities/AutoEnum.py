from enum import Enum


class AutoEnum(Enum):
    """ Auto generate index of enum """
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

'''
Example)

class Color(AutoEnum):
    red = ()
    green = ()
    blue = ()

>>> Color.green.value == 2
True
'''
