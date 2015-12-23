from Utilities import Singleton

class CoreManager(Singleton):
    """
    Manager other mangers classes. ex) shader manager, material manager...
    CoreManager usage for debug what are woring manager..
    """
    def __init__(self):
        self.managers = []

    def regist(self, manager):
        self.managers.append(manager)