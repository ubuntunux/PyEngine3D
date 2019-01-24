import numpy as np

from PyEngine3D.Common import logger
from PyEngine3D.Utilities import Singleton
from GameClient import GameClient


class ScriptManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.resource_manager = None
        self.scene_manager = None
        self.game_client = None

    def initialize(self, core_manager):
        logger.info("ScriptManager::initialize")

        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.scene_manager

        model = self.resource_manager.get_model("skeletal")
        if model is not None:
            main_camera = self.scene_manager.main_camera
            pos = main_camera.transform.pos - main_camera.transform.front * 5.0
            self.obj_instance = self.scene_manager.add_object(model=model, pos=pos)
            self.obj_instance.transform.set_scale(0.01)

        self.game_client = GameClient()

    def exit(self):
        logger.info("ScriptManager::exit")
        self.scene_manager.delete_object(self.obj_instance.name)

    def update(self, dt):
        pass
        # self.game_client.update()
