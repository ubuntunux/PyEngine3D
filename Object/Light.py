import numpy as np

from Utilities import *
from Common import logger
from App import CoreManager
from Object import BaseObject


class Light(BaseObject):
    def __init__(self, name, pos, mesh, material_instance, lightColor=(1.0, 1.0, 1.0, 1.0)):
        BaseObject.__init__(self, name, pos, mesh, material_instance)
        self.lightColor = np.array(lightColor, dtype=np.float32)
