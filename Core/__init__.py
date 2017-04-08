import os

from Utilities import Logger, Config
# logger = Logger.getLogger(level=Logger.INFO)
logger = Logger.getLogger(level=Logger.WARNING)
config = Config(os.path.join(os.path.split(__file__)[0], "Config.ini"))


from .Command import COMMAND, get_command_name, CustomPipe, CustomQueue
from .CoreManager import CoreManager