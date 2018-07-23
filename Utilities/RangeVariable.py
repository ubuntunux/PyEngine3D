import copy
import math
import random

import numpy as np


class RangeVariable:
    def __init__(self, min_value, max_value):
        self.value = None
        self.set_range(min_value, max_value)

    def set_range(self, min_value, max_value):
        if max_value is None:
            max_value = min_value

        min_value, max_value = np.minimum(min_value, max_value), np.maximum(min_value, max_value)

        self.value = np.array([min_value, max_value], dtype=np.float32)

    def get_value(self):
        return np.random.uniform(self.value[0], self.value[1])

    def get_save_data(self):
        save_data = dict(
            min_value=self.value[0].tolist(),
            max_value=self.value[1].tolist()
        )
        return save_data
