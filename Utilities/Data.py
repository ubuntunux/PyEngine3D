
class Data:
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __getattr__(self, attr):
        return self.__dict__.get(attr)

    def get_dict(self) -> dict:
        return self.__dict__

    def set_dict(self, dict_data: dict):
        self.__dict__ = dict_data

'''
Example:
>>> data = Data()
>>> data.x = 99
>>> print(data.x)
99
>>> data.y  # AttributeError does not occur.
None
>>> data.y or 77
77
'''

