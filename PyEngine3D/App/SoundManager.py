import os

import openal

from PyEngine3D.Common import logger, SOUND_DISTANCE_RATIO
from PyEngine3D.Utilities import *


class SoundManager(Singleton):
    def __init__(self):
        self.core_manager = None
        self.resource_manager = None
        self.scene_manager = None
        self.bgm_player = None
        self.interface_sound_list = []
        self.sound_list = []
        self.elapsed_time = 0.0

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.scene_manager = core_manager.scene_manager

        self.sound_listner = openal.oalGetListener()
        self.set_listener_position(Float3(0, 0, 0))
        self.set_listener_forward(Float3(0, 0, 1))

    def close(self):
        openal.oalQuit()

    def clear(self):
        self.set_listener_position(Float3(0, 0, 0))
        self.set_listener_forward(Float3(0, 0, 1))

        self.stop_music()
        for interface_sound in self.interface_sound_list:
            self.stop_sound(interface_sound)
        self.interface_sound_list = []

        for sound in self.sound_list:
            sound.destroy()
        self.sound_list.clear()

    def set_listener_position(self, position):
        self.sound_listner.set_position(tuple(position * SOUND_DISTANCE_RATIO))

    def set_listener_forward(self, forward):
        self.sound_listner.set_orientation(list(forward) + [0.0, 0.0, 1.0])

    def create_sound(self, filepath):
        file_ = openal.WaveFile(filepath)
        buffer_ = openal.Buffer(file_)
        return buffer_

    # bgm
    def play_music(self, music_name, loop=True, volume=1.0, position=None):
        self.stop_music()
        self.bgm_player = self.play_sound(music_name, loop, volume, position)

    def pause_music(self):
        self.pause_sound(self.bgm_player)

    def stop_music(self):
        self.stop_sound(self.bgm_player)
        self.bgm_player = None

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
        sound_buffer = self.resource_manager.get_sound(sound_name)
        if sound_buffer is not None:
            sound = openal.Source(sound_buffer)
            sound.set_looping(loop)
            sound.set_gain(volume)
            if position is not None:
                sound.set_position(tuple(position * SOUND_DISTANCE_RATIO))
            else:
                sound.set_position(self.sound_listner.position)

            sound.play()
            self.sound_list.append(sound)
            return sound
        return None

    def pause_sound(self, sound):
        if sound is not None:
            sound.pause()

    def stop_sound(self, sound):
        if sound is not None:
            sound.stop()

    def update(self, dt):
        index = 0
        sound_count = len(self.sound_list)
        for i in range(sound_count):
            sound = self.sound_list[index]
            if openal.AL_STOPPED == sound.get_state():
                sound.destroy()
                self.sound_list.pop(index)
                continue
            index += 1

        index = 0
        sound_count = len(self.interface_sound_list)
        # for i in range(sound_count):
        #     sound = self.interface_sound_list[index]
        #     if self.game_backend.is_sound_playing(sound):
        #         if self.sound_listner_position is not None:
        #             sound.position = self.sound_listner.position
        #         index += 1
        #     else:
        #         self.stop_interface_sound(sound)
        #         self.interface_sound_list.pop(index)
