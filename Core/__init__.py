import os

from Utilities import Logger, Config
logger = Logger.getLogger(level=Logger.INFO)
# logger = Logger.getLogger(level=Logger.ERROR)
config = Config(os.path.join(os.path.split(__file__)[0], "Config.ini"))

from .Command import *
from .CoreManager import *