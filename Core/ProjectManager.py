import os

from . import logger, log_level, CoreManager, SceneManager
from Resource import ResourceManager
from Utilities import Singleton, GetClassName, Config


class ProjectManager(Singleton):
    def __init__(self):
        self.config = Config(os.path.join(os.path.split(__file__)[0], "test_project.ini"), log_level)
        self.coreManager = None
        self.sceneManager = None
        self.resourceManager = None

    def initialize(self):
        logger.info("initialize " + GetClassName(self))
        self.coreManager = CoreManager.CoreManager.instance()
        self.sceneManager = SceneManager.SceneManager.instance()
        self.resourceManager = ResourceManager.instance()

    def load_project(self, scene_name):
        pass

    def save_project(self):
        pass
