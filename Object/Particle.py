import copy
import time
import math

import numpy as np

from Common import logger
from Object import TransformObject, Model
from Utilities import *
from Common.Constants import *
from Common import logger, log_level, COMMAND
from App import CoreManager


class Particle:
    def __init__(self, name, particle_info):
        self.name = name
        self.particle_info = particle_info
        self.transform = TransformObject()
        self.emitters_group = []
        self.attributes = Attributes()

        self.play()

    def get_save_data(self):
        save_data = dict(
            name=self.name,
            pos=self.transform.pos.tolist(),
            rot=self.transform.rot.tolist(),
            scale=self.transform.scale.tolist()
        )
        return save_data

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)
        self.attributes.set_attribute('pos', self.transform.pos)
        self.attributes.set_attribute('rot', self.transform.rot)
        self.attributes.set_attribute('scale', self.transform.scale)
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        if attribute_name == 'pos':
            self.transform.set_pos(attribute_value)
        elif attribute_name == 'rot':
            self.transform.set_rotation(attribute_value)
        elif attribute_name == 'scale':
            self.transform.set_scale(attribute_value)

        # replay particle
        self.play()

    def play(self):
        self.destroy()

        for emitter_info in self.particle_info.emitter_infos:
            emitters = []
            for i in range(emitter_info.spawn_count):
                emitter = Emitter(emitter_info)
                emitters.append(emitter)
            self.emitters_group.append(emitters)

        for emitters in self.emitters_group:
            for emitter in emitters:
                emitter.play()

    def destroy(self):
        for emitters in self.emitters_group:
            for emitter in emitters:
                emitter.destroy()
        self.emitters_group = []

    def update(self, dt):
        self.transform.update_transform()

        for emitters in self.emitters_group:
            for emitter in emitters:
                emitter.update(self.transform, dt)


class Emitter:
    def __init__(self, emitter_info):
        self.emitter_info = emitter_info
        self.first_time = True
        self.alive = False
        self.elapsed_time = 0.0
        
        # sequence
        self.loop_remain = 0
        self.total_cell_count = 0
        self.current_sequence = [1, 1]
        self.prev_sequence_index = -1

        self.delay = 0.0
        self.life_time = 0.0
        self.play_speed = 0.0
        self.gravity = 0.0
        self.opacity = 1.0
        self.velocity = Float3()
        self.rotation_velocity = Float3()
        self.scale_velocity = Float3()
        self.has_velocity = False
        self.has_rotation_velocity = False
        self.has_scale_velocity = False
        self.transform = TransformObject()
        self.model_matrix = MATRIX4_IDENTITY.copy()
    
    def refresh(self):
        self.loop_remain = self.emitter_info.loop
        self.total_cell_count = self.emitter_info.total_cell_count
        
        self.delay = self.emitter_info.delay.get_value()
        self.life_time = self.emitter_info.life_time.get_value()
        self.play_speed = self.emitter_info.play_speed.get_value()
        self.gravity = self.emitter_info.gravity.get_value()
        self.opacity = self.emitter_info.opacity.get_value()
        self.velocity[...] = self.emitter_info.velocity.get_value()
        self.rotation_velocity[...] = self.emitter_info.rotation_velocity.get_value()
        self.scale_velocity[...] = self.emitter_info.scale_velocity.get_value()

        self.transform.set_pos(self.emitter_info.position.get_value())
        self.transform.set_rotation(self.emitter_info.rotation.get_value())
        self.transform.set_scale(self.emitter_info.scale.get_value())

        self.has_velocity = any([v != 0.0 for v in self.velocity])
        self.has_rotation_velocity = any([v != 0.0 for v in self.rotation_velocity])
        self.has_scale_velocity = any([v != 0.0 for v in self.scale_velocity])

    def play(self):
        self.refresh()

        if 0.0 == self.life_time or 0 == self.loop_remain:
            self.alive = False
            return

        self.alive = True
        self.elapsed_time = 0.0
        self.prev_sequence_index = -1

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

    def update(self, parent_transform, dt):
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

        self.transform.update_transform()

        self.model_matrix[...] = np.dot(self.transform.matrix, parent_transform.matrix)

        if 0.0 != self.emitter_info.fade:
            opacity = life_ratio if 0.0 < self.emitter_info.fade else (1.0 - life_ratio)
            self.opacity = math.pow(opacity, abs(self.emitter_info.fade))


class ParticleInfo:
    def __init__(self, name, emitter_infos):
        self.name = name
        self.emitter_infos = []

        for emitter_info in emitter_infos:
            self.add_emiter(**emitter_info)

        self.attributes = Attributes()

    def add_emiter(self, **emitter_info):
        self.emitter_infos.append(EmitterInfo(**emitter_info))

    def delete_emiter(self, index):
        if index < len(self.emitter_infos):
            self.emitter_infos.pop(index)

    def get_save_data(self):
        save_data = []
        for emitter_info in self.emitter_infos:
            save_data.append(emitter_info.get_save_data())
        return save_data

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)
        attributes = []
        for emitter_info in self.emitter_infos:
            attributes.append(emitter_info.get_attribute())
        self.attributes.set_attribute('emitter_infos', attributes)
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        item_info_history = []
        while parent_info is not None:
            item_info_history.insert(0, parent_info)
            parent_info = parent_info.parent_info

        if 1 < len(item_info_history) and 'emitter_infos' == item_info_history[0].attribute_name:
            emitter_index = item_info_history[1].index
            emitter_info = self.emitter_infos[emitter_index]
            count = len(item_info_history)
            if 2 == count:
                emitter_info.set_attribute(attribute_name, attribute_value, parent_info, attribute_index)
            else:
                emitter_attribute = getattr(emitter_info, item_info_history[2].attribute_name)
                if type(emitter_attribute) in (tuple, list, np.ndarray):
                    emitter_info.set_attribute(attribute_name, attribute_value, parent_info, attribute_index)
                elif isinstance(emitter_attribute, RangeVariable):
                    if 'min_value' == attribute_name:
                        emitter_attribute.set_range(attribute_value, emitter_attribute.max_value)
                    elif 'max_value' == attribute_name:
                        emitter_attribute.set_range(emitter_attribute.min_value, attribute_value)
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)

    def refresh_attribute_info(self):
        CoreManager.instance().send(COMMAND.TRANS_RESOURCE_ATTRIBUTE, self.get_attribute())

    def add_component(self, attribute_name, parent_info, attribute_index):
        if 'emitter_infos' == attribute_name:
            self.add_emiter()
            self.refresh_attribute_info()

    def delete_component(self, attribute_name, parent_info, attribute_index):
        if parent_info is not None and 'emitter_infos' == parent_info.attribute_name:
            self.delete_emiter(attribute_index)
            self.refresh_attribute_info()


class EmitterInfo:
    def __init__(self, **emitter_info):
        self.emitter_info = emitter_info
        self.name = emitter_info.get('name', 'Emitter')
        self.enable = emitter_info.get('enable', True)
        self.spawn_count = emitter_info.get('spawn_count', 1)
        self.billboard = emitter_info.get('billboard', True)
        self.mesh = emitter_info.get('mesh')
        self.material_instance = emitter_info.get('material_instance')
        self.fade = emitter_info.get('fade', 0.0)  # negative is fade out, 0.0 is none, positive is fade in

        # sequence
        self.loop = emitter_info.get('loop', -1)  # -1 is infinite
        self.cell_count = emitter_info.get('cell_count', [1, 1])
        self.total_cell_count = self.cell_count[0] * self.cell_count[1]

        # variance
        self.delay = RangeVariable(**emitter_info.get('delay', dict(min_value=0.0, max_value=0.0)))
        self.life_time = RangeVariable(**emitter_info.get('life_time', dict(min_value=1.0, max_value=5.0)))
        self.play_speed = RangeVariable(**emitter_info.get('play_speed', dict(min_value=0.0, max_value=0.0)))
        self.gravity = RangeVariable(**emitter_info.get('gravity', dict(min_value=0.0, max_value=0.0)))
        self.opacity = RangeVariable(**emitter_info.get('opacity', dict(min_value=1.0, max_value=1.0)))
        self.velocity = RangeVariable(
            **emitter_info.get('velocity', dict(min_value=FLOAT3_ZERO, max_value=FLOAT3_ZERO)))
        self.rotation_velocity = RangeVariable(
            **emitter_info.get('rotation_velocity', dict(min_value=FLOAT3_ZERO, max_value=FLOAT3_ZERO)))
        self.scale_velocity = RangeVariable(
            **emitter_info.get('scale_velocity', dict(min_value=FLOAT3_ZERO, max_value=FLOAT3_ZERO)))
        self.position = RangeVariable(
            **emitter_info.get('position', dict(min_value=FLOAT3_ZERO, max_value=FLOAT3_ZERO)))
        self.rotation = RangeVariable(
            **emitter_info.get('rotation', dict(min_value=FLOAT3_ZERO, max_value=FLOAT3_ZERO)))
        self.scale = RangeVariable(
            **emitter_info.get('scale', dict(min_value=Float3(1.0, 1.0, 1.0), max_value=Float3(1.0, 1.0, 1.0))))
        self.attributes = Attributes()

    def get_save_data(self):
        save_data = dict(
            enable=self.enable,
            spawn_count=self.spawn_count,
            billboard=self.billboard,
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instance=self.material_instance.name if self.material_instance is not None else '',
            fade=self.fade,
            loop=self.loop,
            cell_count=self.cell_count,
            delay=self.delay.get_save_data(),
            life_time=self.life_time.get_save_data(),
            play_speed=self.play_speed.get_save_data(),
            gravity=self.gravity.get_save_data(),
            opacity=self.opacity.get_save_data(),
            velocity=self.velocity.get_save_data(),
            rotation_velocity=self.rotation_velocity.get_save_data(),
            scale_velocity=self.scale_velocity.get_save_data(),
            position=self.position.get_save_data(),
            rotation=self.rotation.get_save_data(),
            scale=self.scale.get_save_data(),
        )
        return save_data

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)

        attributes = self.get_save_data()
        keys = list(attributes.keys())
        keys.sort()
        for key in keys:
            self.attributes.set_attribute(key, attributes[key])
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        if hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)

            if 'mesh' == attribute_name:
                self.mesh = CoreManager.instance().resource_manager.get_mesh(attribute_value)
            elif 'material_instance' == attribute_name:
                self.material_instance = CoreManager.instance().resource_manager.get_material_instance (attribute_value)
