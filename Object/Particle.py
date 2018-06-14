import copy
import time
import math

import numpy as np

from Common import logger
from Object import TransformObject, Model
from Utilities import *
from Common.Constants import *
from App import CoreManager


class ParticleManager(Singleton):
    def __init__(self):
        self.active = True
        self.particles = []
        self.active_particles = []

    def clear(self):
        for particle in self.active_particles:
            particle.destroy()

        self.particles = []
        self.active_particles = []

    def create_particle(self, particle_infos):
        particle = Particle(particle_infos)
        self.particles.append(particle)
        particle.play()

    def destroy_particle(self, particle):
        particle.destroy()
        self.active_particles.remove(particle)

    def update(self, dt):
        for particle in self.active_particles:
            particle.update(dt)


class Particle:
    def __init__(self, name, emitters_infos=[]):
        self.emitters_list = []

        for emitters_info in emitters_infos:
            count = emitter_info.get('count', 1)
            emitter_list = []
            self.emitters_list.append(emitter_list)

            for i in range(count):
                emitter = Emitter(emitters_info)
                emitter_list.append(emitter)

    def get_save_data(self):
        save_data = [emitter.get_save_data() for emitter in self.emitters_list]
        return save_data

    def play(self):
        for emitter_list in self.emitters_list:
            for emitter in emitter_list:
                emitter.play()

    def destroy(self):
        for emitter_list in self.emitters_list:
            for emitter in emitter_list:
                emitter.destroy()
        self.emitters_list = []

    def update(self, dt):
        for emitter_list in self.emitters_list:
            for emitter in emitter_list:
                emitter.update(dt)


class Emitter:
    def __init__(self, **emitter_info):
        self.name = emitter_info.get('name', 'Emitter')
        self.first_time = True
        self.alive = False
        self.elapsed_time = 0.0
        self.has_velocity = False
        self.has_rotation_velocity = False
        self.has_scale_velocity = False
        self.billboard = emitter_info.get('billboard', True)
        self.mesh = None
        self.material_instance = None
        self.transform = TransformObject()
        self.fade = emitter_info.get('fade', 0.0)  # negative is fade out, 0.0 is none, positive is fade in

        # sequence
        self.loop = emitter_info.get('loop', 1)  # -1 is infinite
        self.loop_remain = self.loop
        self.cell_count = emitter_info.get('cell_count', [1, 1])
        self.total_cell_count = self.cell_count[0] * self.cell_count[1]
        self.current_sequence = [1, 1]
        self.prev_sequence_index = -1

        # variance
        self.variance_delay = RangeVariable(emitter_info.get('delay', 0.0))
        self.variance_life_time = RangeVariable(emitter_info.get('life_time', 0.0))
        self.variance_play_speed = RangeVariable(emitter_info.get('play_speed', 0.0))
        self.variance_gravity = RangeVariable(emitter_info.get('gravity', 0.0))
        self.variance_opacity = RangeVariable(emitter_info.get('opacity', 1.0))
        self.variance_velocity = RangeVariable(emitter_info.get('velocity', FLOAT3_ZERO))
        self.variance_rotation_velocity = RangeVariable(emitter_info.get('rotation_velocity', FLOAT3_ZERO))
        self.variance_scale_velocity = RangeVariable(emitter_info.get('scale_velocity', FLOAT3_ZERO))
        self.variance_position = RangeVariable(emitter_info.get('position', FLOAT3_ZERO))
        self.variance_rotation = RangeVariable(emitter_info.get('rotation', FLOAT3_ZERO))
        self.variance_scale = RangeVariable(emitter_info.get('scale', Float3(1.0, 1.0, 1.0)))

        self.delay = 0.0
        self.life_time = 0.0
        self.play_speed = 0.0
        self.gravity = 0.0
        self.opacity = 1.0
        self.velocity = Float3()
        self.rotation_velocity = Float3()
        self.scale_velocity = Float3()

        self.attributes = Attributes()

    def get_save_data(self):
        save_data = dict(
            billboard=self.billboard,
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instance=self.material_instance.name if self.material_instance is not None else '',
            fade=self.fade,
            loop=self.loop,
            cell_count=self.cell_count,
            delay=self.variance_delay.get_save_data(),
            life_time=self.variance_life_time.get_save_data(),
            play_speed=self.variance_play_speed.get_save_data(),
            gravity=self.variance_gravity.get_save_data(),
            opacity=self.variance_opacity.get_save_data(),
            velocity=self.variance_velocity.get_save_data(),
            rotation_velocity=self.variance_rotation_velocity.get_save_data(),
            scale_velocity=self.variance_scale_velocity.get_save_data(),
            position=self.variance_position.get_save_data(),
            rotation=self.variance_rotation.get_save_data(),
            scale=self.variance_scale.get_save_data(),
        )
        return save_data

    def get_attribute(self):
        attributes = self.get_save_data()
        self.attributes.set_attribute('name', self.name)
        for key in attributes:
            self.attributes.set_attribute(key, attributes[key])
        return self.attributes

    def set_attribute(self, attributeName, attributeValue, attribute_index):
        if hasattr(self, "variance_" + attributeName):
            variance_value = getattr("variance_" + attributeName)
            variance_value.set_value(*attributeValue)
        elif hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)
        self.play()
        
    def refresh(self):
        self.delay = self.variance_delay.get_value()
        self.life_time = self.variance_life_time.get_value()
        self.play_speed = self.variance_play_speed.get_value()
        self.gravity = self.variance_gravity.get_value()
        self.opacity = self.variance_opacity.get_value()
        self.velocity[...] = self.variance_velocity.get_value()
        self.rotation_velocity[...] = self.variance_rotation_velocity.get_value()
        self.scale_velocity[...] = self.variance_scale_velocity.get_value()

        self.transform.set_pos(self.variance_position.get_value())
        self.transform.set_rotation(self.variance_rotation.get_value())
        self.transform.set_scale(self.variance_scale.get_value())

        self.has_velocity = any([v != 0.0 for v in self.velocity])
        self.has_rotation_velocity = any([v != 0.0 for v in self.rotation_velocity])
        self.has_scale_velocity = any([v != 0.0 for v in self.scale_velocity])

    def play(self):
        if 0.0 == self.life_time or 0 == self.loop:
            self.alive = False
            return

        self.alive = True
        self.loop_remain = self.loop
        self.elapsed_time = 0.0
        self.prev_sequence_index = -1
        self.total_cell_count = self.cell_count[0] * self.cell_count[1]
        self.refresh()

    def destroy(self):
        self.alive = False

    def update_sequence(self, life_ratio):
        if self.total_cell_count > 1 and self.play_speed > 0:
            ratio = (life_ratio * self.play_speed) % 1.0
            index = min(self.total_cell_count, int(math.floor((self.total_cell_count - 1) * ratio)))

            if index == self.prev_sequence_index:
                return

            self.prev_sequence_index = index
            self.current_sequence[0] = index % self.cell_count[0]
            self.current_sequence[1] = self.cell_count[1] - int(index / self.cell_count[0]) - 1

    def update(self, dt):
        if not self.alive:
            return

        if 0.0 < self.delay:
            self.delay -= dt
            if self.delay < 0.0:
                self.delay = 0.0
            else:
                return

        self.elapsed_time += dt

        if self.life_time < self.elapsed_time:
            self.elapsed_time %= self.life_time

            if self.loop_remain > 0:
                self.loop_remain -= 1

            if self.loop_remain == 0:
                self.destroy()
                return

            self.refresh()

        life_ratio = 0.0
        if 0.0 < self.life_time:
            life_ratio = self.elapsed_time / self.life_time

        self.update_sequence(life_ratio)

        if 0.0 != self.gravity:
            self.velocity[1] -= self.gravity * dt

        # update transform
        if self.has_velocity:
            self.transform.move(self.velocity * dt)

        if self.has_rotation_velocity:
            self.transform.rotation(self.rotation_velocity * dt)

        if self.has_scale_velocity:
            self.transform.scaling(self.scale_velocity * dt)

        if 0.0 != self.fade:
            opacity = life_ratio if 0.0 < self.fade else (1.0 - life_ratio)
            self.opacity = math.pow(opacity, abs(self.fade))