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
        self.project_file_name = ""

    def initialize(self):
        logger.info("initialize " + GetClassName(self))
        self.coreManager = CoreManager.CoreManager.instance()
        self.sceneManager = SceneManager.SceneManager.instance()
        self.resourceManager = ResourceManager.instance()

    def new_project(self, filename):
        try:
            if filename:
                self.project_file_name = filename
                print("new ", self.project_file_name)
                return
        except:
            logger.error("Failed save %s." % filename)

    def open_project(self, filename):
        try:
            if os.path.exists(filename):
                print("open ", filename)
                self.project_file_name = filename
                return
        except:
            logger.error("Failed open %s." % filename)

    def save_project(self):
        try:
            if self.project_file_name:
                print("save ", self.project_file_name)
                return
            else:
                self.coreManager.request_save_as_project()
        except:
            logger.error("Failed save %s." % filename)

    def save_as_project(self, filename):
        try:
            if filename:
                self.project_file_name = filename
                print("save ", self.project_file_name)
                return
        except:
            logger.error("Failed save %s." % filename)