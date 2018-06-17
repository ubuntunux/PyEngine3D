import copy

import numpy as np


class RangeVariable:
    def __init__(self, values):
        self.is_array = False
        self.v1, self.v2 = values
        self.range = None
        self.min = None
        self.max = None

        self.set_value(self.v1, self.v2)

    def set_value(self, v1, v2=None):
        self.is_array = hasattr(v1, '__len__')

        # list or tuple or array
        if self.is_array:
            self.v1 = np.array(v1, dtype=np.float32)
            self.v2 = self.v1.copy() if v2 is None else np.array(v2, dtype=np.float32)
            self.range = range(len(v1))
            self.min = np.minimum(self.v1, self.v2)
            self.max = np.maximum(self.v1, self.v2)
        else:
            self.v1 = float(v1)
            self.v2 = float(v1 if v2 is None else v2)
            self.range = range(1)
            self.min = min(self.v1, self.v2)
            self.max = max(self.v1, self.v2)

        if self.is_array:
            if any([x != y for x, y in zip(v1, v2)]):
                self.get_value = self.get_random_array
        elif v1 != v2:
            self.get_value = self.get_random

    def get_value(self):
        return self.v1

    def get_random(self):
        return random.uniform(self.v1, self.v2)

    def get_random_array(self):
        return [random.uniform(self.v1[i], self.v2[i]) for i in self.range]

    def get_save_data(self):
        if self.is_array:
            return self.min.tolist(), self.max.tolist()
        else:
            return self.min, self.max
