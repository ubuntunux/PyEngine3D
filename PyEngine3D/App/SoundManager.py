import os

from PyEngine3D.Common import logger
from PyEngine3D.Utilities import *


class SoundManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.sound_list = []

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.game_backend = core_manager.game_backend
        self.resource_manager = core_manager.resource_manager

    def play_sound(self, sound_name):
        sound = self.resource_manager.get_sound(sound_name)
        if sound is not None:
            self.game_backend.play_sound(sound)

    def update(self, dt):
        pass
