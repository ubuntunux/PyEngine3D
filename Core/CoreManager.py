from Utilities import Singleton

#------------------------------#
# CLASS : MaterialManager
#------------------------------#
class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """
    managers = []

    def initialize(self):
        self.managers = []

    def regist(self, manager):
        self.managers.append(manager)

#------------------------------#
# Globals
#------------------------------#
CoreManager = CoreManager.instance()