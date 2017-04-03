import numpy as np

from Utilities import *
from Core import logger, config
from Object import StaticMesh


class Light(StaticMesh):
    def __init__(self, name, pos, mesh, material_instance, lightColor=(1.0, 1.0, 1.0, 1.0)):
        StaticMesh.__init__(self, name, pos, mesh, material_instance)
        self.lightColor = np.array(lightColor, dtype=np.float32)
