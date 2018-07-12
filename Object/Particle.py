import copy
import time
import math

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from Common import logger
from Object import TransformObject, Model
from OpenGLContext import InstanceBuffer
from Utilities import *
from Common.Constants import *
from Common import logger, log_level, COMMAND
from App import CoreManager
from .RenderOptions import BlendMode


class ParticleManager(Singleton):
    def __init__(self):
        self.particles = []
        self.active_particles = []
        self.render_particles = []

    def get_save_data(self):
        return [particle.get_save_data() for particle in self.particles]

    def clear(self):
        for particle in self.particles:
            particle.destroy()

        self.particles = []
        self.active_particles = []

    def add_particle(self, particle):
        self.particles.append(particle)
        self.play_particle(particle)
        return particle

    def delete_particle(self, particle):
        self.destroy_particle(particle)
        self.particles.remove(particle)

    def play_particle(self, particle):
        if particle not in self.active_particles:
            self.active_particles.append(particle)
        particle.play()

    def destroy_particle(self, particle):
        if particle in self.active_particles:
            self.active_particles.remove(particle)
        particle.destroy()

    def notify_particle_info_changed(self, particle_info):
        for particle in self.particles:
            if particle_info == particle.particle_info:
                self.play_particle(particle)

    def render(self):
        glEnable(GL_BLEND)

        for particle in self.render_particles:
            for i, emitter_info in enumerate(particle.particle_info.emitter_infos):
                if not emitter_info.enable:
                    continue

                # set blend mode
                if emitter_info.blend_mode is BlendMode.BLEND:
                    glBlendEquation(GL_FUNC_ADD)
                    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                elif emitter_info.blend_mode is BlendMode.ADDITIVE:
                    glBlendEquation(GL_FUNC_ADD)
                    glBlendFunc(GL_ONE, GL_ONE)
                elif emitter_info.blend_mode is BlendMode.MULTIPLY:
                    glBlendEquation(GL_FUNC_ADD)
                    glBlendFunc(GL_DST_COLOR, GL_ZERO)
                elif emitter_info.blend_mode is BlendMode.MULTIPLY:
                    glBlendEquation(GL_FUNC_SUBTRACT)
                    glBlendFunc(GL_ONE, GL_ONE)

                material_instance = emitter_info.material_instance
                material_instance.use_program()
                material_instance.bind_material_instance()
                material_instance.bind_uniform_data('texture_diffuse', emitter_info.texture_diffuse)

                material_instance.bind_uniform_data('particle_matrix', particle.transform.matrix)
                material_instance.bind_uniform_data('billboard', emitter_info.billboard)
                material_instance.bind_uniform_data('color', emitter_info.color)
                material_instance.bind_uniform_data('blend_mode', emitter_info.blend_mode.value)
                material_instance.bind_uniform_data('sequence_width', 1.0 / emitter_info.cell_count[0])
                material_instance.bind_uniform_data('sequence_height', 1.0 / emitter_info.cell_count[1])

                geometry = emitter_info.mesh.get_geometry()

                draw_count = 0
                for emitter in particle.emitters_group[i]:
                    if emitter.is_renderable():
                        emitter_info.instance_data_0[draw_count][...] = emitter.transform.matrix
                        emitter_info.instance_data_1[draw_count][0:2] = emitter.sequence_uv
                        emitter_info.instance_data_1[draw_count][2:4] = emitter.next_sequence_uv
                        emitter_info.instance_data_2[draw_count][0] = emitter.sequence_ratio
                        emitter_info.instance_data_2[draw_count][1] = emitter.final_opacity
                        draw_count += 1

                if 0 < draw_count:
                    emitter_info.instance_buffer.bind_instance_buffer(emitter_info.instance_data_0,
                                                                        emitter_info.instance_data_1,
                                                                        emitter_info.instance_data_2)
                    geometry.draw_elements_instanced(draw_count)

    def view_frustum_culling_particle(self, camera, particle):
        to_particle = particle.transform.pos - camera.transform.pos
        radius = particle.particle_info.radius * max(particle.transform.scale)
        for i in range(4):
            d = np.dot(camera.frustum_vectors[i], to_particle)
            if radius < d:
                return True
        return False

    def update(self, dt):
        main_camera = CoreManager.instance().scene_manager.main_camera
        self.render_particles = []

        for particle in self.active_particles:
            particle.update(dt)

            if particle.alive:
                if not self.view_frustum_culling_particle(main_camera, particle):
                    self.render_particles.append(particle)
            else:
                self.destroy_particle(particle)


class Particle:
    def __init__(self, **particle_data):
        self.name = particle_data.get('name', 'particle')
        self.particle_info = particle_data.get('particle_info')

        self.transform = TransformObject()
        self.transform.set_pos(particle_data.get('pos', (0.0, 0.0, 0.0)))
        self.transform.set_rotation(particle_data.get('rot', (0.0, 0.0, 0.0)))
        self.transform.set_scale(particle_data.get('scale', (1.0, 1.0, 1.0)))

        self.alive = False
        self.emitters_group = []
        self.attributes = Attributes()

    def get_save_data(self):
        save_data = dict(
            name=self.name,
            pos=self.transform.pos.tolist(),
            rot=self.transform.rot.tolist(),
            scale=self.transform.scale.tolist(),
            particle_info=self.particle_info.name if self.particle_info is not None else ''
        )
        return save_data

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)
        self.attributes.set_attribute('pos', self.transform.pos)
        self.attributes.set_attribute('rot', self.transform.rot)
        self.attributes.set_attribute('scale', self.transform.scale)
        self.attributes.set_attribute('particle_info',
                                      self.particle_info.name if self.particle_info is not None else '')
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
        self.sequence_uv = [0.0, 0.0]
        self.next_sequence_uv = [0.0, 0.0]
        self.sequence_ratio = 0.0
        self.sequence_index = 0
        self.next_sequence_index = 0

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
        self.total_cell_count = self.emitter_info.cell_count[0] * self.emitter_info.cell_count[1]
        
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
        self.sequence_ratio = 0.0
        self.sequence_index = 0
        self.next_sequence_index = 0

    def destroy(self):
        self.alive = False

    def is_renderable(self):
        return self.alive and (0.0 == self.delay)

    def update_sequence(self, life_ratio):
        if 1 < self.total_cell_count and 0 < self.play_speed:
            ratio = life_ratio * self.play_speed
            ratio = self.total_cell_count * (ratio - math.floor(ratio))
            index = math.floor(ratio)
            next_index = (index + 1) % self.total_cell_count
            self.sequence_ratio = ratio - index

            if next_index == self.next_sequence_index:
                return

            cell_count = self.emitter_info.cell_count
            self.sequence_index = self.next_sequence_index
            self.sequence_uv[0] = self.next_sequence_uv[0]
            self.sequence_uv[1] = self.next_sequence_uv[1]
            self.next_sequence_index = next_index
            self.next_sequence_uv[0] = (next_index % cell_count[0]) / cell_count[0]
            self.next_sequence_uv[1] = (cell_count[1] - 1 - int(math.floor(next_index / cell_count[0]))) / cell_count[1]

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
    def __init__(self, name, **particle_info):
        self.name = name
        self.radius = particle_info.get('radius', 1.0)

        self.emitter_infos = []

        for emitter_info in particle_info.get('emitter_infos', []):
            self.add_emiter(**emitter_info)

        self.attributes = Attributes()

    def add_emiter(self, **emitter_info):
        self.emitter_infos.append(EmitterInfo(**emitter_info))
        # refresh
        ParticleManager.instance().notify_particle_info_changed(self)

    def delete_emiter(self, index):
        if index < len(self.emitter_infos):
            self.emitter_infos.pop(index)
        # refresh
        ParticleManager.instance().notify_particle_info_changed(self)

    def get_save_data(self):
        save_data = dict(radius=self.radius,
                         emitter_infos=[])

        for emitter_info in self.emitter_infos:
            save_data['emitter_infos'].append(emitter_info.get_save_data())
        return save_data

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)
        self.attributes.set_attribute('radius', self.radius)
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
        # refresh
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
        self.blend_mode = BlendMode(emitter_info.get('blend_mode', 0))
        self.enable = emitter_info.get('enable', True)
        self.gpu_particle = emitter_info.get('gpu_particle', False)
        self.spawn_count = emitter_info.get('spawn_count', 1)
        self.billboard = emitter_info.get('billboard', True)
        self.color = emitter_info.get('color', Float3(1.0, 1.0, 1.0))
        self.fade_in = emitter_info.get('fade_in', 0.0)  # if 0.0 is none else curve
        self.fade_out = emitter_info.get('fade_out', 0.0)

        resource_manager = CoreManager.instance().resource_manager
        default_mesh = resource_manager.get_default_mesh()
        default_material_instance = resource_manager.get_default_particle_material_instance()
        texture_white = resource_manager.get_texture('common.flat_white')

        self.mesh = emitter_info.get('mesh') or default_mesh
        self.material_instance = emitter_info.get('material_instance') or default_material_instance
        self.texture_diffuse = emitter_info.get('texture_diffuse') or texture_white

        # sequence
        self.loop = emitter_info.get('loop', -1)  # -1 is infinite
        self.cell_count = emitter_info.get('cell_count', [1, 1])

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

        # instance data
        self.instance_buffer = InstanceBuffer(name="instance_buffer",
                                              location_offset=5,
                                              element_datas=[MATRIX4_IDENTITY, FLOAT4_ZERO, FLOAT4_ZERO])
        self.instance_data_0 = None
        self.instance_data_1 = None
        self.instance_data_2 = None

        self.attributes = Attributes()

        self.set_spawn_count(self.spawn_count)

    def set_spawn_count(self, spawn_count):
        self.spawn_count = spawn_count
        self.instance_data_0 = np.array([MATRIX4_IDENTITY, ] * self.spawn_count, dtype=np.float32)
        self.instance_data_1 = np.array([FLOAT4_ZERO, ] * self.spawn_count, dtype=np.float32)
        self.instance_data_2 = np.array([FLOAT4_ZERO, ] * self.spawn_count, dtype=np.float32)

    def get_save_data(self):
        save_data = dict(
            enable=self.enable,
            blend_mode=self.blend_mode.value,
            spawn_count=self.spawn_count,
            billboard=self.billboard,
            color=self.color,
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instance=self.material_instance.name if self.material_instance is not None else '',
            texture_diffuse=self.texture_diffuse.name if self.texture_diffuse is not None else '',
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
            if 'blend_mode' == key:
                self.attributes.set_attribute(key, BlendMode(self.blend_mode.value))
            else:
                self.attributes.set_attribute(key, attributes[key])
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        if hasattr(self, attribute_name):
            resource_manager = CoreManager.instance().resource_manager
            if 'mesh' == attribute_name:
                mesh = resource_manager.get_mesh(attribute_value)
                if mesh is not None:
                    self.mesh = mesh
            elif 'material_instance' == attribute_name:
                material_instance = resource_manager.get_material_instance(attribute_value)
                if material_instance is not None:
                    self.material_instance = material_instance
            elif 'texture_diffuse' == attribute_name:
                texture_diffuse = resource_manager.get_texture(attribute_value)
                if texture_diffuse is not None:
                    self.texture_diffuse = texture_diffuse
            elif 'spawn_count' == attribute_name:
                self.set_spawn_count(attribute_value)
            elif 'cell_count' == attribute_name:
                self.cell_count = [max(1, x) for x in attribute_value]
            else:
                setattr(self, attribute_name, attribute_value)
