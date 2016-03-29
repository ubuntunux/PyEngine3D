# default logger
from Utilities import Logger
logger = Logger.getLogger('default', 'logs', False)

# config
from Configure import Config
config = Config("Config.ini")

from Core.Command import CMD, PipeRecvSend, PipeSendRecv
from Core.CoreManager import *