import copy
import math
import random

import numpy as np


class RangeVariable:
    def __init__(self, min_value, max_value):
        self.is_array = False
        self.min_value = None
        self.max_value = None

        self.set_range(min_value, max_value)

    def set_range(self, min_value, max_value):
        self.is_array = hasattr(min_value, '__len__')

        # list or tuple or array
        if self.is_array:
            min_value = np.array(min_value, dtype=np.float32)
            max_value = min_value.copy() if max_value is None else np.array(max_value, dtype=np.float32)
            self.min_value = np.minimum(min_value, max_value)
            self.max_value = np.maximum(min_value, max_value)
        else:
            min_value = float(min_value)
            max_value = float(min_value if max_value is None else max_value)
            self.min_value = min(min_value, max_value)
            self.max_value = max(min_value, max_value)

        if self.is_array:
            if any([x != y for x, y in zip(self.min_value, self.max_value)]):
                self.get_value = self.get_random_array
        elif min_value != max_value:
            self.get_value = self.get_random

    def get_value(self):
        return self.min_value

    def get_random(self):
        return random.uniform(self.min_value, self.max_value)

    def get_random_array(self):
        return [random.uniform(x, y) for x, y in zip(self.min_value, self.max_value)]

    def get_save_data(self):
        save_data = dict()

        if self.is_array:
            save_data['min_value'] = self.min_value.tolist()
            save_data['max_value'] = self.max_value.tolist()
            return save_data
        else:
            save_data['min_value'] = self.min_value
            save_data['max_value'] = self.max_value
            return save_data
