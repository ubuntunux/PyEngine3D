import platform

from Configure import Config
from Utilities import Logger, Singleton

# default logger
logger = Logger.getLogger('default', 'logs', False)

# config
config = Config("Config.ini")

#------------------------------#
# CLASS : CoreManager
#------------------------------#
class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """

    def __init__(self):
        self.running = False
        self.managers = {}

        # timer
        self.fpsLimit = 1.0 / 60.0
        self.fps = 0.0
        self.delta = 0.0
        self.currentTime = 0.0

    def initialize(self):
        logger.info('Platform : %s' % platform.platform())
        logger.info('initialize : %s' % self.__class__.__name__)

    def regist(self, mgrName, manager):
        if mgrName in self.managers:
            errorMsg = mgrName + " is already in managers."
            logger.error(errorMsg)
            raise Exception(errorMsg)
        self.managers[mgrName] = manager

    def getManager(self, mgrName):
        return self.managers[mgrName]

    def getManagers(self):
        return self.managers

    def update(self):
        logger.info("Process Start : %s" % self.__class__.__name__)

        self.running = True
        while self.running:
            continue

        logger.info("Process Stop : %s" % self.__class__.__name__)



#------------------------------#
# Globals
#------------------------------#
coreManager = CoreManager.instance()