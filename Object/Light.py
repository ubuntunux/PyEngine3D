import numpy as np

from Utilities import *
from Common import logger
from App import CoreManager
from Object import StaticActor


class Light(StaticActor):
    def __init__(self, name, **object_data):
        StaticActor.__init__(self, name, **object_data)
        lightColor = object_data.get('lightColor', (1.0, 1.0, 1.0, 1.0))
        self.lightColor = np.array(lightColor, dtype=np.float32)
