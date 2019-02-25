from PyEngine3D.Common import logger
from PyEngine3D.Utilities import Singleton


class ScriptManager(Singleton):
    def __init__(self):
        logger.info("ScriptManager::__init__")

    def initialize(self, core_manager):
        logger.info("ScriptManager::initialize")

    def exit(self):
        logger.info("ScriptManager::exit")

    def update(self, delta):
        pass

