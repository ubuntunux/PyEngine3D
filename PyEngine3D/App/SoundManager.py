import os

from PyEngine3D.Common import logger, SOUND_DISTANCE_RATIO
from PyEngine3D.Utilities import *


class SoundManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.game_backend = None
        self.resource_manager = None
        self.scene_manager = None
        self.bgm_player = None
        self.interface_sound_list = []
        self.elapsed_time = 0.0

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.game_backend = core_manager.game_backend
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.scene_manager

        self.sound_listner = core_manager.game_backend.create_sound_listner()
        self.sound_listner.position = (0, 0, 0)
        self.sound_listner.up_orientation = (0, 1, 0)
        self.sound_listner.forward_orientation = (0, 0, 1)

    def clear(self):
        self.sound_listner.position = (0, 0, 0)
        self.stop_music()
        for interface_sound in self.interface_sound_list:
            self.stop_sound(interface_sound)
        self.interface_sound_list = []

    def set_listener_position(self, position):
        self.sound_listner.position = tuple(position * SOUND_DISTANCE_RATIO)

    def set_listener_forward(self, forward):
        self.sound_listner.forward_orientation = tuple(forward)

    # bgm
    def play_music(self, music_name, loop=True, volume=1.0, position=None):
        self.stop_music()

        self.bgm_player = self.play_sound(music_name, loop, volume, position)

    def pause_music(self):
        self.pause_sound(self.bgm_player)

    def stop_music(self):
        self.stop_sound(self.bgm_player)

    # interface sound
    def play_interface_sound(self, sound_name, loop=True, volume=1.0):
        sound = self.play_sound(sound_name, loop, volume)
        self.interface_sound_list.append(sound)

    def pause_interface_sound(self, sound):
        self.pause_sound(sound)

    def stop_interface_sound(self, sound):
        self.stop_sound(sound)

    # commonm sound
    def play_sound(self, sound_name, loop=False, volume=1.0, position=None):
        sound = self.resource_manager.get_sound(sound_name)
        if sound is not None:
            sound_player = self.game_backend.play_sound(sound, loop, volume, position)
            return sound_player
        return None

    def pause_sound(self, sound_player):
        if sound_player is not None:
            self.game_backend.pause_sound(sound_player)

    def stop_sound(self, sound_player):
        if sound_player is not None:
            self.game_backend.stop_sound(sound_player)

    def update(self, dt):
        index = 0
        sound_count = len(self.interface_sound_list)
        for i in range(sound_count):
            sound = self.interface_sound_list[index]
            if self.game_backend.is_sound_playing(sound):
                if self.sound_listner_position is not None:
                    sound.position = self.sound_listner.position
                index += 1
            else:
                self.stop_interface_sound(sound)
                self.interface_sound_list.pop(index)
