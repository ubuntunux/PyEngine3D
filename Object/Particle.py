import copy
import time
import math

import numpy as np

from Common import logger
from Object import TransformObject, Model
from OpenGLContext import InstanceBuffer
from Utilities import *
from Common.Constants import *
from Common import logger, log_level, COMMAND
from App import CoreManager


class ParticleManager(Singleton):
    def __init__(self):
        self.particles = []
        self.active_particles = []

    def clear(self):
        for particle in self.particles:
            particle.destroy()

        self.particles = []
        self.active_particles = []

    def add_particle(self, name, particle_info):
        particle = Particle(name, particle_info)
        self.particles.append(particle)
        self.play_particle(particle)
        return particle

    def remove_particle(self, particle):
        self.particles.pop(particle)

    def play_particle(self, particle):
        if particle not in self.active_particles:
            self.active_particles.append(particle)
        particle.play()

    def destroy_particle(self, particle):
        if particle in self.active_particles:
            self.active_particles.pop(particle)
        particle.destroy()

    def notify_particle_info_changed(self, particle_info):
        for particle in self.particles:
            if particle_info == particle.particle_info:
                self.play_particle(particle)

    def render(self):
        for particle in self.active_particles:
            for i, emitter_info in enumerate(particle.particle_info.emitter_infos):
                if not emitter_info.enable:
                    continue

                material_instance = emitter_info.material_instance
                material_instance.use_program()
                material_instance.bind_material_instance()
                material_instance.bind_uniform_data('particle_matrix', particle.transform.matrix)

                material_instance.bind_uniform_data('opacity', 1.0)

                geometry = emitter_info.mesh.get_geometry()
                geometry.bind_vertex_buffer()

                instance_data_model = []
                instance_data_opacity = []
                emiiters = particle.emitters_group[i]
                for emiiter in emiiters:
                    if emiiter.is_renderable():
                        instance_data_model.append(emiiter.transform.matrix)
                        instance_data_opacity.append([emiiter.final_opacity, 0.0, 0.0, 0.0])

                instance_data_model = np.array(instance_data_model, dtype=np.float32)
                instance_data_opacity = np.array(instance_data_opacity, dtype=np.float32)

                emitter_info.instance_buffer_model.bind_instance_buffer(instance_data=instance_data_model,
                                                                        divisor=1)

                emitter_info.instance_buffer_opacity.bind_instance_buffer(instance_data=instance_data_opacity,
                                                                          divisor=1)

                geometry.draw_elements_instanced(len(instance_data_model))

    def update(self, dt):
        for particle in self.active_particles:
            particle.update(dt)

            if not particle.alive:
                self.destroy_particle(particle)


class Particle:
    def __init__(self, name, particle_info):
        self.name = name
        self.particle_info = particle_info
        self.transform = TransformObject()
        self.alive = False
        self.emitters_group = []
        self.attributes = Attributes()

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

        self.alive = True

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
        self.alive = False

        for emitters in self.emitters_group:
            for emitter in emitters:
                emitter.destroy()
        self.emitters_group = []

    def update(self, dt):
        if not self.alive:
            return

        self.transform.update_transform()

        is_alive = self.alive

        for emitters in self.emitters_group:
            for emitter in emitters:
                emitter.update(dt)
                is_alive = is_alive or emitter.alive

        if not is_alive:
            self.destroy()


class Emitter:
    def __init__(self, emitter_info):
        self.emitter_info = emitter_info
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

        self.transform = TransformObject()
        self.has_velocity = False
        self.has_rotation_velocity = False
        self.has_scale_velocity = False
        self.final_opacity = 1.0
    
    def refresh(self):
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
        self.final_opacity = self.opacity

    def play(self):
        self.refresh()

        if 0.0 == self.life_time:
            self.alive = False
            return

        self.alive = True
        self.loop_remain = self.emitter_info.loop
        self.elapsed_time = 0.0
        self.prev_sequence_index = -1

    def destroy(self):
        self.alive = False

    def is_renderable(self):
        return self.alive and (0.0 == self.delay)

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

            if 0 < self.loop_remain:
                self.loop_remain -= 1

            if 0 == self.loop_remain:
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

        if 0.0 != self.emitter_info.fade_in or 0.0 != self.emitter_info.fade_out:
            fade_in = math.pow(life_ratio, self.emitter_info.fade_in)
            fade_out = math.pow(1.0 - life_ratio, self.emitter_info.fade_out)
            self.final_opacity = (fade_in * (1.0 - life_ratio) + fade_out * life_ratio) * self.opacity


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

        ParticleManager.instance().notify_particle_info_changed(self)

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
        self.fade_in = emitter_info.get('fade_in', 0.0)  # if 0.0 is none else curve
        self.fade_out = emitter_info.get('fade_out', 0.0)

        resource_manager = CoreManager.instance().resource_manager
        default_mesh = resource_manager.get_default_mesh()
        default_material_instance = resource_manager.get_default_effect_material_instance()
        self.mesh = emitter_info.get('mesh') or default_mesh
        self.material_instance = emitter_info.get('material_instance') or default_material_instance

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

        self.instance_buffer_model = InstanceBuffer(name="model",
                                                    layout_location=5,
                                                    element_data=np.zeros(16, dtype=np.float32))

        self.instance_buffer_opacity = InstanceBuffer(name="opacity",
                                                      layout_location=9,
                                                      element_data=FLOAT4_ZERO)

        self.attributes = Attributes()

    def get_save_data(self):
        save_data = dict(
            enable=self.enable,
            spawn_count=self.spawn_count,
            billboard=self.billboard,
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instance=self.material_instance.name if self.material_instance is not None else '',
            fade_in=self.fade_in,
            fade_out=self.fade_out,
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
            if 'mesh' == attribute_name:
                mesh = CoreManager.instance().resource_manager.get_mesh(attribute_value)
                if mesh is not None:
                    self.mesh = mesh
            elif 'material_instance' == attribute_name:
                material_instance = CoreManager.instance().resource_manager.get_material_instance(attribute_value)
                if material_instance is not None:
                    self.material_instance = material_instance
            else:
                setattr(self, attribute_name, attribute_value)
