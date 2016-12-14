import numpy as np

from Core import logger, config
from Utilities import *
from Object import BaseObject

#
# CLASS : Light
#
class Light(BaseObject):
    def __init__(self, name, pos, mesh, material, lightColor = (1.0, 1.0, 1.0, 1.0)):
        BaseObject.__init__(self, name, pos, mesh, material)

        self.lightColor = np.array(lightColor, dtype=np.float32)

        # log
        logger.info("Create Light : %s" % self.name)