import os
import traceback
import configparser

from . import logger, log_level, CoreManager, SceneManager
from ResourceManager import ResourceManager, DefaultProjectFile
from Utilities import Singleton, GetClassName, Config


class ProjectManager(Singleton):
    def __init__(self):
        self.coreManager = None
        self.sceneManager = None
        self.resourceManager = None
        self.project_name = ""
        self.project_dir = ""
        self.project_filename = ""
        self.config = None
        self.next_open_project_filename = ""

    def initialize(self, project_filename=""):
        # default project
        if project_filename == "":
            project_filename = DefaultProjectFile
        else:
            project_filename = os.path.relpath(project_filename, ".")

        logger.info("initialize %s : %s" % (GetClassName(self), project_filename))
        try:
            self.next_open_project_filename = ""
            self.project_name = os.path.splitext(os.path.split(project_filename)[1])[0]
            self.project_dir = os.path.split(project_filename)[0]
            self.project_filename = project_filename
            self.config = Config(project_filename, log_level)

            # set default config
            self.config.setDefaultValue("Screen", "size", [1024, 768])
            self.config.setDefaultValue("Camera", "fov", 45)
            self.config.setDefaultValue("Camera", "near", 0.1)
            self.config.setDefaultValue("Camera", "far", 1000)
            self.config.setDefaultValue("Camera", "move_speed", 50.0)
            self.config.setDefaultValue("Camera", "pan_speed", 5.0)
            self.config.setDefaultValue("Camera", "rotation_speed", 0.3)
        except:
            logger.info("Cannot open %s : %s" % (GetClassName(self), project_filename))
            return False

        self.coreManager = CoreManager.CoreManager.instance()
        self.sceneManager = SceneManager.SceneManager.instance()
        self.resourceManager = ResourceManager.ResourceManager.instance()
        return True

    def new_project(self, new_project_dir):
        try:
            if new_project_dir:
                project_name = new_project_dir.split(os.sep)[-1]
                self.resourceManager.new_project(new_project_dir)

                default_project_filename = os.path.join(new_project_dir, os.path.split(DefaultProjectFile)[1])
                project_filename = os.path.join(new_project_dir, project_name + ".project")
                if os.path.exists(default_project_filename) and not os.path.exists(project_filename):
                    os.rename(default_project_filename, project_filename)
                else:
                    config = Config(project_filename, log_level)
                    config.save()

                self.open_project_next_time(project_filename)
        except:
            logger.error(traceback.format_exc())

    def open_project_next_time(self, project_filename):
        try:
            if os.path.exists(project_filename):
                # will be open
                self.next_open_project_filename = project_filename
                self.coreManager.close()
                return
        except:
            logger.error(traceback.format_exc())
        if project_filename:
            logger.error("Failed open %s." % project_filename)

    def save_project(self):
        try:
            if self.config and self.project_filename != DefaultProjectFile:
                main_camera = self.coreManager.sceneManager.getMainCamera()
                if main_camera:
                    main_camera.write_to_config(self.config)
                self.config.save()
            return
        except:
            logger.error(traceback.format_exc())
        if self.project_filename:
            logger.error("Failed save %s." % self.project_filename)

    def close_project(self):
        self.save_project()
