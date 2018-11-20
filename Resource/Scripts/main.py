from PyEngine3D.Common import logger
from PyEngine3D.Utilities import Singleton


class ScriptManager(Singleton):
    def __init__(self):
        self.core_manager = None

    def initialize(self, core_manager):
        self.core_manager = core_manager

    def exit(self):
        pass

    def update(self, dt):
        pass
