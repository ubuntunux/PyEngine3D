import platform

from Utilities import Logger, Singleton

logger = Logger.getLogger('default', 'logs', False)

#------------------------------#
# CLASS : CoreManager
#------------------------------#
class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """
    managers = {}
    logger = None

    def initialize(self):
        logger.info('Platform : %s' % platform.platform())
        self.managers = {}

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


#------------------------------#
# Globals
#------------------------------#
coreManager = CoreManager.instance()