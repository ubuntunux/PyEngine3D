from Common import logger
from Utilities import Singleton


class BaseScriptManager(Singleton):
    def __init__(self):
        self.core_manager = None

    def initialize(self, core_manager):
        self.core_manager = core_manager

    def update(self, dt):
        pass


class ScriptManager(BaseScriptManager):
    def __init__(self):
        super().__init__()

    def initialize(self, core_manager):
        super().initialize(core_manager)

    def update(self, dt):
        pass
