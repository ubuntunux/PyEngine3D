import copy
import math
import random

import numpy as np


class RangeVariable:
    def __init__(self, min_value, max_value=None):
        self.value = None
        self.min_value = None
        self.max_value = None
        self.set_range(min_value, max_value)

    def set_range(self, min_value, max_value=None):
        if max_value is None:
            max_value = min_value

        self.value = np.array([min_value, max_value], dtype=np.float32)
        self.min_value = np.minimum(self.value[0], self.value[1])
        self.max_value = np.maximum(self.value[0], self.value[1])

    def get_value(self):
        return self.value

    def get_min(self):
        return self.min_value

    def get_max(self):
        return self.max_value

    def get_uniform(self):
        return np.random.uniform(self.value[0], self.value[1])

    def get_save_data(self):
        save_data = dict(
            min_value=self.value[0].tolist(),
            max_value=self.value[1].tolist()
        )
        return save_data
