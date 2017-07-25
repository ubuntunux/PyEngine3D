from enum import Enum


class AutoEnum(Enum):
    """ Auto generate index of enum """
    def __new__(cls):
        value = int(len(cls.__members__))
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @classmethod
    def convert_index_to_enum(cls, index):
        for obj in cls.__members__.values():
            if obj.value == index:
                return obj
        return None


'''
Example)

class Color(AutoEnum):
    red = ()
    green = ()
    blue = ()

>>> Color.green.value == 2
True
'''
