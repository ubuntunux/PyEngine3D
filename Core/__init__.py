# default logger
from Utilities import Logger
logger = Logger.getLogger(level=Logger.INFO)

# config
from Configure import Config
config = Config("Config.ini")

from .Command import *
from .CoreManager import *