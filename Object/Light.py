import numpy as np

from Core import logger, config
from Utilities import *
from Object import StaticMesh


class Light(StaticMesh):
    def __init__(self, name, pos, mesh, material_instance, lightColor=(1.0, 1.0, 1.0, 1.0)):
        StaticMesh.__init__(self, name, pos, mesh, material_instance)

        self.lightColor = np.array(lightColor, dtype=np.float32)

        # log
        logger.info("Create Light : %s" % self.name)