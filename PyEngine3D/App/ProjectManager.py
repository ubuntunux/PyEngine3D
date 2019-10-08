import os
import sys
import traceback
import configparser

from PyEngine3D.Common import logger, log_level
from PyEngine3D.Utilities import Singleton, GetClassName, Config


class ProjectManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.scene_manager = None
        self.resource_manager = None
        self.project_name = ""
        self.project_dir = ""
        self.project_filename = ""
        self.config = None
        self.next_open_project_filename = ""

    def initialize(self, core_manager, project_filename=""):
        self.core_manager = core_manager
        self.scene_manager = core_manager.scene_manager
        self.resource_manager = core_manager.resource_manager

        # default project
        if project_filename == "":
            project_filename = self.resource_manager.DefaultProjectFile
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
            self.config.setDefaultValue("Screen", "size", [1280, 720])
            self.config.setDefaultValue("Screen", "full_screen", False)
            meter_per_unit = 1.0  # 1 unit = 1 m
            self.config.setDefaultValue("Camera", "meter_per_unit", meter_per_unit)
            self.config.setDefaultValue("Camera", "near", 0.1 / meter_per_unit)  # 10 cm
            self.config.setDefaultValue("Camera", "far", 2000.0 / meter_per_unit)  # 2 km
            self.config.setDefaultValue("Camera", "fov", 60)
            self.config.setDefaultValue("Camera", "move_speed", meter_per_unit)
            self.config.setDefaultValue("Camera", "pan_speed", meter_per_unit)
            self.config.setDefaultValue("Camera", "rotation_speed", 0.005)
        except BaseException:
            logger.info("Cannot open %s : %s" % (GetClassName(self), project_filename))
            return False
        return True

    def restart(self):
        self.open_project_next_time(self.project_filename)

    def new_project(self, new_project_dir):
        try:
            if new_project_dir:
                project_name = os.path.split(new_project_dir)[-1]
                self.resource_manager.prepare_project_directory(new_project_dir)

                default_project_filename = os.path.join(new_project_dir,
                                                        os.path.split(self.resource_manager.DefaultProjectFile)[1])
                project_filename = os.path.join(new_project_dir, project_name + ".project")
                if os.path.exists(default_project_filename) and not os.path.exists(project_filename):
                    os.rename(default_project_filename, project_filename)
                else:
                    config = Config(project_filename, log_level)
                    config.save()

                self.open_project_next_time(project_filename)
        except BaseException:
            logger.error(traceback.format_exc())

    def open_project_next_time(self, project_filename):
        try:
            if os.path.exists(project_filename):
                # will be open
                self.next_open_project_filename = project_filename
                self.core_manager.close()
                return
        except BaseException:
            logger.error(traceback.format_exc())
        if project_filename:
            logger.error("Failed open %s." % project_filename)

    def save_project(self):
        try:
            if self.config and self.project_filename != self.resource_manager.DefaultProjectFile:
                main_camera = self.core_manager.scene_manager.main_camera
                if main_camera:
                    main_camera.write_to_config(self.config)
                self.config.save()
            return
        except BaseException:
            logger.error(traceback.format_exc())
        if self.project_filename:
            logger.error("Failed save %s." % self.project_filename)

    def close_project(self):
        self.save_project()
