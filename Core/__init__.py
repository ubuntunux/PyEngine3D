import os

# use local sdl library file path
sdlpath = os.path.join(os.path.dirname(__file__), 'libs')
if os.path.exists(sdlpath):
    os.environ['PYSDL2_DLL_PATH'] = sdlpath

# default logger
from Utilities import Logger
logger = Logger.getLogger('default', 'logs', False)

# config
from Configure import Config
config = Config("Config.ini")

from Core.Command import CMD, PipeRecvSend, PipeSendRecv
from Core.CoreManager import *