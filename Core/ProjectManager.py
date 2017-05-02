import os
import traceback

from . import logger, log_level, CoreManager, SceneManager
from ResourceManager import ResourceManager
from Utilities import Singleton, GetClassName, Config


class ProjectManager(Singleton):
    def __init__(self):
        self.config = Config(os.path.join(os.path.split(__file__)[0], "test_project.ini"), log_level)
        self.coreManager = None
        self.sceneManager = None
        self.resourceManager = None
        self.project_name = ""
        self.project_filename = ""
        self.open_project_filename = ""

    def initialize(self, project_filename):
        logger.info("initialize %s : %s" % (GetClassName(self), project_filename))
        self.open_project_filename = ""
        self.project_name = os.path.splitext(os.path.split(project_filename)[1])[0]
        self.project_filename = project_filename

        self.coreManager = CoreManager.CoreManager.instance()
        self.sceneManager = SceneManager.SceneManager.instance()
        self.resourceManager = ResourceManager.instance()
        return True

    def new_project(self, new_project_dir):
        try:
            if new_project_dir:
                project_name = new_project_dir.split(os.sep)[-1]
                self.resourceManager.new_project(new_project_dir)

                project_filename = os.path.join(new_project_dir, project_name + ".project")
                f = open(project_filename, "w")
                f.writelines("%s project" % project_name)
                f.close()

                self.open_project_next_time(project_filename)
        except:
            logger.error("Failed save %s." % project_name)
            logger.error(traceback.format_exc())

    def open_project_next_time(self, project_filename):
        try:
            if os.path.exists(project_filename):
                # will be open
                self.open_project_filename = project_filename
                self.coreManager.open_project_next_time()
        except:
            logger.error("Failed open %s." % filename)
            logger.error(traceback.format_exc())

    def save_project(self):
        try:
            print("save ", self.project_filename)
        except:
            logger.error("Failed save %s." % filename)
            logger.error(traceback.format_exc())
