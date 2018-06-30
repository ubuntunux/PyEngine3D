from Common import logger
from Utilities import Singleton


class ScriptManager(Singleton):
    def __init__(self):
        self.core_manager = None

    def initialize(self, core_manager):
        self.core_manager = core_manager

    def update(self, dt):
        pass
