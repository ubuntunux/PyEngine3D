import copy
import time
import math

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from Common import logger
from Object import TransformObject, Model
from OpenGLContext import AtomicCounterBuffer, ShaderStorageBuffer, InstanceBuffer, UniformBlock
from Utilities import *
from Common.Constants import *
from Common import logger, log_level, COMMAND
from App import CoreManager
from .RenderOptions import BlendMode


class ParticleManager(Singleton):
    USE_ATOMIC_COUNTER = False

    def __init__(self):
        self.renderer = None
        self.particles = []
        self.active_particles = []
        self.render_particles = []
        self.resource_manager = None
        self.emitter_instance_buffer = None

        self.material_gpu_particle = None
        self.material_gpu_update = None

    def initialize(self, core_manager):
        self.renderer = core_manager.renderer
        self.resource_manager = core_manager.resource_manager

        self.emitter_instance_buffer = InstanceBuffer(name="instance_buffer",
                                                      location_offset=5,
                                                      element_datas=[MATRIX4_IDENTITY,
                                                                     MATRIX4_IDENTITY,
                                                                     FLOAT4_ZERO,
                                                                     FLOAT4_ZERO])

        self.material_gpu_particle = self.resource_manager.get_material_instance('fx.gpu_particle')
        self.material_gpu_update = self.resource_manager.get_material_instance('fx.gpu_particle_update')

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
        prev_blend_mode = None

        for particle in self.render_particles:
            for i, emitter_info in enumerate(particle.particle_info.emitter_infos):
                if not emitter_info.enable:
                    continue

                # set blend mode
                if prev_blend_mode != emitter_info.blend_mode:
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
                    prev_blend_mode = emitter_info.blend_mode

                geometry = emitter_info.mesh.get_geometry()

                # emitter common
                uniform_data = self.renderer.uniform_emitter_common_data
                uniform_data['EMITTER_COLOR'] = emitter_info.color
                uniform_data['EMITTER_BILLBOARD'] = emitter_info.billboard
                uniform_data['EMITTER_CELL_COUNT'] = emitter_info.cell_count
                uniform_data['EMITTER_LOOP'] = emitter_info.loop
                uniform_data['EMITTER_BLEND_MODE'] = emitter_info.blend_mode.value
                self.renderer.uniform_emitter_common_buffer.bind_uniform_block(data=uniform_data)

                if emitter_info.enable_gpu_particle:
                    # GPU Particle
                    uniform_data = self.renderer.uniform_emitter_infos_data
                    uniform_data['EMITTER_USE_ATOMIC_COUNTER'] = ParticleManager.USE_ATOMIC_COUNTER
                    uniform_data['EMITTER_PARENT_MATRIX'] = particle.transform.matrix
                    uniform_data['EMITTER_PARENT_INVERSE_MATRIX'] = particle.transform.inverse_matrix
                    uniform_data['EMITTER_DELAY'] = emitter_info.delay.value
                    uniform_data['EMITTER_LIFE_TIME'] = emitter_info.life_time.value
                    uniform_data['EMITTER_TRANSFORM_POSITION_MIN'] = emitter_info.transform_position.value[0]
                    uniform_data['EMITTER_FORCE_GRAVITY'] = emitter_info.force_gravity
                    uniform_data['EMITTER_TRANSFORM_POSITION_MAX'] = emitter_info.transform_position.value[1]
                    uniform_data['EMITTER_FADE_IN'] = emitter_info.fade_in
                    uniform_data['EMITTER_TRANSFORM_ROTATION_MIN'] = emitter_info.transform_rotation.value[0]
                    uniform_data['EMITTER_FADE_OUT'] = emitter_info.fade_out
                    uniform_data['EMITTER_TRANSFORM_ROTATION_MAX'] = emitter_info.transform_rotation.value[1]
                    uniform_data['EMITTER_OPACITY'] = emitter_info.opacity
                    uniform_data['EMITTER_TRANSFORM_SCALE_MIN'] = emitter_info.transform_scale.value[0]
                    uniform_data['EMITTER_PLAY_SPEED'] = emitter_info.play_speed
                    uniform_data['EMITTER_TRANSFORM_SCALE_MAX'] = emitter_info.transform_scale.value[1]
                    uniform_data['EMITTER_VELOCITY_POSITION_MIN'] = emitter_info.velocity_position.value[0]
                    uniform_data['EMITTER_VELOCITY_POSITION_MAX'] = emitter_info.velocity_position.value[1]
                    uniform_data['EMITTER_VELOCITY_ROTATION_MIN'] = emitter_info.velocity_rotation.value[0]
                    uniform_data['EMITTER_VELOCITY_ROTATION_MAX'] = emitter_info.velocity_rotation.value[1]
                    uniform_data['EMITTER_VELOCITY_SCALE_MIN'] = emitter_info.velocity_scale.value[0]
                    uniform_data['EMITTER_VELOCITY_SCALE_MAX'] = emitter_info.velocity_scale.value[1]
                    uniform_data['EMITTER_ENABLE_VECTOR_FIELD'] = emitter_info.enable_vector_field
                    uniform_data['EMITTER_VECTOR_FIELD_STRENGTH'] = emitter_info.vector_field_strength
                    uniform_data['EMITTER_VECTOR_FIELD_TIGHTNESS'] = emitter_info.vector_field_tightness
                    uniform_data['EMITTER_VECTOR_FIELD_MATRIX'] = emitter_info.vector_field_transform.matrix
                    uniform_data['EMITTER_VECTOR_FIELD_INV_MATRIX'] = emitter_info.vector_field_transform.inverse_matrix

                    self.renderer.uniform_emitter_infos_buffer.bind_uniform_block(data=uniform_data)

                    for emitter in particle.emitters_group[i]:
                        if emitter.alive:
                            render_count = emitter_info.spawn_count
                            is_infinite = emitter.is_infinite()

                            # update gpu particle
                            material_instance = self.material_gpu_update
                            material_instance.use_program()
                            material_instance.bind_material_instance()

                            if emitter_info.enable_vector_field:
                                material_instance.bind_uniform_data('texture_vector_field',
                                                                    emitter_info.texture_vector_field)

                            # set gpu buffer
                            emitter.emitter_gpu_buffer.bind_storage_buffer()

                            # reset to 0
                            if not is_infinite and ParticleManager.USE_ATOMIC_COUNTER:
                                emitter.emitter_counter_buffer.bind_atomic_counter_buffer(data=emitter.emitter_counter)

                            glDispatchCompute(render_count, 1, 1)
                            glMemoryBarrier(GL_ATOMIC_COUNTER_BARRIER_BIT | GL_SHADER_STORAGE_BARRIER_BIT)

                            if not is_infinite and ParticleManager.USE_ATOMIC_COUNTER:
                                # too slow..
                                emitter.gpu_particle_count = emitter.emitter_counter_buffer.get_buffer_data()

                            # render gpu particle
                            material_instance = self.material_gpu_particle
                            material_instance.use_program()
                            material_instance.bind_material_instance()
                            material_instance.bind_uniform_data('texture_diffuse', emitter_info.texture_diffuse)

                            geometry.draw_elements_instanced(render_count)
                else:
                    # CPU Particle
                    material_instance = emitter_info.material_instance
                    material_instance.use_program()
                    material_instance.bind_material_instance()
                    material_instance.bind_uniform_data('texture_diffuse', emitter_info.texture_diffuse)

                    draw_count = 0
                    for emitter in particle.emitters_group[i]:
                        if emitter.is_renderable():
                            emitter_info.parent_matrix_data[draw_count][...] = emitter.parent_matrix
                            emitter_info.matrix_data[draw_count][...] = emitter.transform.matrix
                            emitter_info.uvs_data[draw_count][0:2] = emitter.sequence_uv
                            emitter_info.uvs_data[draw_count][2:4] = emitter.next_sequence_uv
                            emitter_info.sequence_opacity_data[draw_count][0] = emitter.sequence_ratio
                            emitter_info.sequence_opacity_data[draw_count][1] = emitter.final_opacity
                            draw_count += 1

                    if 0 < draw_count:
                        self.emitter_instance_buffer.bind_instance_buffer(datas=[emitter_info.parent_matrix_data,
                                                                                 emitter_info.matrix_data,
                                                                                 emitter_info.uvs_data,
                                                                                 emitter_info.sequence_opacity_data])
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

    def play(self):
        self.destroy()

        self.alive = True

        for emitter_info in self.particle_info.emitter_infos:
            emitters = []
            if emitter_info.enable_gpu_particle:
                emitter = Emitter(self, emitter_info)
                emitters.append(emitter)
            else:
                for i in range(emitter_info.spawn_count):
                    emitter = Emitter(self, emitter_info)
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

        self.transform.update_transform(update_inverse_matrix=True)

        is_alive = self.alive

        for emitters in self.emitters_group:
            for emitter in emitters:
                emitter.update(dt)
                is_alive = is_alive or emitter.alive

        if not is_alive:
            self.destroy()


class Emitter:
    def __init__(self, parent, emitter_info):
        self.parent = parent
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
        self.velocity_position = Float3()
        self.velocity_rotation = Float3()
        self.velocity_scale = Float3()

        self.has_velocity_position = False
        self.has_velocity_rotation = False
        self.has_velocity_scale = False

        self.final_opacity = 1.0
        self.force = Float3()

        self.transform = TransformObject()
        self.parent_matrix = MATRIX4_IDENTITY.copy()

        # gpu data
        self.emitter_gpu_data = None
        self.emitter_gpu_buffer = None
        self.emitter_counter = None
        self.emitter_counter_buffer = None
        self.gpu_particle_count = 0

    def refresh(self):
        self.total_cell_count = self.emitter_info.cell_count[0] * self.emitter_info.cell_count[1]

        if self.emitter_info.enable_gpu_particle:
            # GPU Particle
            self.gpu_particle_count = self.emitter_info.spawn_count
            self.delay = self.emitter_info.delay.get_max()
            self.life_time = self.emitter_info.life_time.get_max()
        else:
            # CPU Particle
            self.delay = self.emitter_info.delay.get_uniform()
            self.life_time = self.emitter_info.life_time.get_uniform()

            self.velocity_position[...] = self.emitter_info.velocity_position.get_uniform()
            self.velocity_rotation[...] = self.emitter_info.velocity_rotation.get_uniform()
            self.velocity_scale[...] = self.emitter_info.velocity_scale.get_uniform()

            self.transform.set_pos(self.emitter_info.transform_position.get_uniform())
            self.transform.set_rotation(self.emitter_info.transform_rotation.get_uniform())
            self.transform.set_scale(self.emitter_info.transform_scale.get_uniform())

            # Store metrics at the time of spawn.
            self.parent_matrix[...] = self.parent.transform.matrix

            # We will apply inverse_matrix here because we will apply parent_matrix later.
            self.force[...] = np.dot([0.0, -self.emitter_info.force_gravity, 0.0, 1.0],
                                     self.parent.transform.inverse_matrix)[:3]

            self.has_velocity_position = \
                any([v != 0.0 for v in self.velocity_position]) or self.emitter_info.force_gravity != 0.0
            self.has_velocity_rotation = any([v != 0.0 for v in self.velocity_rotation])
            self.has_velocity_scale = any([v != 0.0 for v in self.velocity_scale])

            self.final_opacity = self.emitter_info.opacity

        # gpu buffer
        if self.emitter_info.enable_gpu_particle:
            self.create_gpu_buffer()
        else:
            self.delete_gpu_buffer()

    def create_gpu_buffer(self):
        self.delete_gpu_buffer()

        count = self.emitter_info.spawn_count

        self.emitter_gpu_data = np.zeros(count, dtype=[('parent_matrix', np.float32, 16),
                                                       ('local_matrix', np.float32, 16),
                                                       ('delay', np.float32),
                                                       ('life_time', np.float32),
                                                       ('opacity', np.float32),
                                                       ('elapsed_time', np.float32),
                                                       ('sequence_uv', np.float32, 2),
                                                       ('next_sequence_uv', np.float32, 2),
                                                       ('sequence_ratio', np.float32),
                                                       ('sequence_index', np.int32),
                                                       ('next_sequence_index', np.int32),
                                                       ('loop_remain', np.int32),
                                                       ('force', np.float32, 3),
                                                       ('state', np.int32),
                                                       ('transform_position', np.float32, 3), ('dummy_1', np.float32),
                                                       ('transform_rotation', np.float32, 3), ('dummy_2', np.float32),
                                                       ('transform_scale', np.float32, 3), ('dummy_3', np.float32),
                                                       ('velocity_position', np.float32, 3), ('dummy_4', np.float32),
                                                       ('velocity_rotation', np.float32, 3), ('dummy_5', np.float32),
                                                       ('velocity_scale', np.float32, 3), ('dummy_6', np.float32)])

        self.emitter_gpu_buffer = ShaderStorageBuffer('emitter_buffer', 0, data=self.emitter_gpu_data)

        self.emitter_counter = np.zeros(1, np.uint32)
        self.emitter_counter_buffer = AtomicCounterBuffer("emitter_counter", 1, data=self.emitter_counter)

    def delete_gpu_buffer(self):
        self.emitter_gpu_data = None
        if self.emitter_gpu_buffer is not None:
            self.emitter_gpu_buffer.delete()
            self.emitter_gpu_buffer = None

        if self.emitter_counter is not None:
            self.emitter_counter[0] = 0

        if self.emitter_counter_buffer is not None:
            self.emitter_counter_buffer.delete()
            self.emitter_counter_buffer = None

    def play(self):
        self.refresh()

        if 0.0 == self.life_time or 0 == self.emitter_info.loop:
            self.destroy()
            return

        self.alive = True
        self.loop_remain = self.emitter_info.loop
        self.elapsed_time = 0.0
        self.sequence_ratio = 0.0
        self.sequence_index = 0
        self.next_sequence_index = 0

    def destroy(self):
        self.alive = False
        self.delete_gpu_buffer()

    def is_renderable(self):
        return self.alive and (0.0 == self.delay)

    def is_infinite(self):
        return self.loop_remain < 0

    def update_sequence(self, life_ratio):
        if 1 < self.total_cell_count and 0 < self.emitter_info.play_speed:
            ratio = life_ratio * self.emitter_info.play_speed
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

        # gpu particle - atomic counter manage
        if self.emitter_info.enable_gpu_particle and ParticleManager.USE_ATOMIC_COUNTER:
            if 0 == self.gpu_particle_count and not self.is_infinite():
                self.destroy()
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

        # gpu particle - application manage
        if self.emitter_info.enable_gpu_particle and not ParticleManager.USE_ATOMIC_COUNTER:
            return

        life_ratio = 0.0
        if 0.0 < self.life_time:
            life_ratio = self.elapsed_time / self.life_time

        self.update_sequence(life_ratio)

        # update transform
        if self.emitter_info.force_gravity != 0.0:
            self.velocity_position += self.force * dt

        if self.has_velocity_position:
            self.transform.move(self.velocity_position * dt)

        if self.has_velocity_rotation:
            self.transform.rotation(self.velocity_rotation * dt)

        if self.has_velocity_scale:
            self.transform.scaling(self.velocity_scale * dt)

        self.transform.update_transform()

        if 0.0 != self.emitter_info.fade_in or 0.0 != self.emitter_info.fade_out:
            self.final_opacity = self.emitter_info.opacity

            left_life_time = self.life_time - self.elapsed_time

            if 0.0 < self.emitter_info.fade_in and self.life_time < self.emitter_info.fade_in:
                self.final_opacity *= self.life_time / self.emitter_info.fade_in

            if 0.0 < self.emitter_info.fade_out and left_life_time < self.emitter_info.fade_out:
                self.final_opacity *= left_life_time / self.emitter_info.fade_out


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
                if hasattr(emitter_info, item_info_history[2].attribute_name):
                    emitter_attribute = getattr(emitter_info, item_info_history[2].attribute_name)
                    if type(emitter_attribute) in (tuple, list, np.ndarray):
                        emitter_info.set_attribute(attribute_name, attribute_value, parent_info, attribute_index)
                    elif isinstance(emitter_attribute, RangeVariable):
                        if 'min_value' == attribute_name:
                            emitter_attribute.set_range(attribute_value, emitter_attribute.value[1])
                        elif 'max_value' == attribute_name:
                            emitter_attribute.set_range(emitter_attribute.value[0], attribute_value)
                else:
                    emitter_info.set_attribute(attribute_name, attribute_value, parent_info, attribute_index)

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
        self.enable_gpu_particle = emitter_info.get('enable_gpu_particle', True)
        self.spawn_count = emitter_info.get('spawn_count', 1)
        self.billboard = emitter_info.get('billboard', True)
        self.color = emitter_info.get('color', Float3(1.0, 1.0, 1.0))
        self.play_speed = emitter_info.get('play_speed', 0.0)
        self.opacity = emitter_info.get('opacity', 1.0)
        self.fade_in = emitter_info.get('fade_in', 0.0)  # if 0.0 is none else curve
        self.fade_out = emitter_info.get('fade_out', 0.0)

        resource_manager = CoreManager.instance().resource_manager
        default_mesh = resource_manager.get_default_mesh()
        default_material_instance = resource_manager.get_default_particle_material_instance()
        texture_white = resource_manager.get_texture('common.flat_white')

        self.mesh = emitter_info.get('mesh') or default_mesh
        self.material_instance = emitter_info.get('material_instance') or default_material_instance
        self.texture_diffuse = emitter_info.get('texture_diffuse') or texture_white

        self.loop = emitter_info.get('loop', -1)  # -1 is infinite
        self.cell_count = np.array(emitter_info.get('cell_count', [1, 1]), dtype=np.int32)

        self.delay = RangeVariable(**emitter_info.get('delay', dict(min_value=0.0)))
        self.life_time = RangeVariable(**emitter_info.get('life_time', dict(min_value=1.0)))
        self.transform_position = RangeVariable(**emitter_info.get('transform_position', dict(min_value=FLOAT3_ZERO)))
        self.transform_rotation = RangeVariable(**emitter_info.get('transform_rotation', dict(min_value=FLOAT3_ZERO)))
        self.transform_scale = RangeVariable(
            **emitter_info.get('transform_scale', dict(min_value=Float3(1.0, 1.0, 1.0))))
        self.velocity_position = RangeVariable(**emitter_info.get('velocity_position', dict(min_value=FLOAT3_ZERO)))
        self.velocity_rotation = RangeVariable(**emitter_info.get('velocity_rotation', dict(min_value=FLOAT3_ZERO)))
        self.velocity_scale = RangeVariable(**emitter_info.get('velocity_scale', dict(min_value=FLOAT3_ZERO)))

        self.force_gravity = emitter_info.get('force_gravity', 0.0)

        self.enable_vector_field = emitter_info.get('enable_vector_field', False)
        texture_vector_field_name = emitter_info.get('texture_vector_field', 'common.default_3d')
        self.texture_vector_field = resource_manager.get_texture_or_none(texture_vector_field_name)
        self.vector_field_strength = emitter_info.get('vector_field_strength', 1.0)
        self.vector_field_tightness = emitter_info.get('vector_field_tightness', 0.1)

        self.vector_field_position = emitter_info.get('vector_field_position', Float3(0.0, 0.0, 0.0))
        self.vector_field_rotation = emitter_info.get('vector_field_rotation', Float3(0.0, 0.0, 0.0))
        self.vector_field_scale = emitter_info.get('vector_field_scale', Float3(1.0, 1.0, 1.0))
        self.vector_field_transform = TransformObject()
        self.update_vector_field_matrix()

        self.parent_matrix_data = None
        self.matrix_data = None
        self.uvs_data = None
        self.sequence_opacity_data = None

        self.attributes = Attributes()

        self.set_spawn_count(self.spawn_count)

    def set_spawn_count(self, spawn_count):
        self.spawn_count = spawn_count
        self.parent_matrix_data = np.zeros(self.spawn_count, dtype=(np.float32, (4, 4)))
        self.matrix_data = np.zeros(self.spawn_count, dtype=(np.float32, (4, 4)))
        self.uvs_data = np.zeros(self.spawn_count, dtype=(np.float32, 4))
        self.sequence_opacity_data = np.zeros(self.spawn_count, dtype=(np.float32, 4))

    def update_vector_field_matrix(self):
        self.vector_field_transform.set_pos(self.vector_field_position)
        self.vector_field_transform.set_rotation(self.vector_field_rotation)
        self.vector_field_transform.set_scale(self.vector_field_scale)
        self.vector_field_transform.update_transform(update_inverse_matrix=True)

    def get_save_data(self):
        save_data = dict(
            enable=self.enable,
            blend_mode=self.blend_mode.value,
            spawn_count=self.spawn_count,
            billboard=self.billboard,
            color=self.color,
            enable_gpu_particle=self.enable_gpu_particle,
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instance=self.material_instance.name if self.material_instance is not None else '',
            texture_diffuse=self.texture_diffuse.name if self.texture_diffuse is not None else '',
            play_speed=self.play_speed,
            opacity=self.opacity,
            fade_in=self.fade_in,
            fade_out=self.fade_out,
            loop=self.loop,
            cell_count=self.cell_count.tolist(),
            delay=self.delay.get_save_data(),
            life_time=self.life_time.get_save_data(),
            transform_position=self.transform_position.get_save_data(),
            transform_rotation=self.transform_rotation.get_save_data(),
            transform_scale=self.transform_scale.get_save_data(),
            velocity_position=self.velocity_position.get_save_data(),
            velocity_rotation=self.velocity_rotation.get_save_data(),
            velocity_scale=self.velocity_scale.get_save_data(),
            force_gravity=self.force_gravity,
            enable_vector_field=self.enable_vector_field,
            vector_field_position=self.vector_field_position,
            vector_field_rotation=self.vector_field_rotation,
            vector_field_scale=self.vector_field_scale,
            vector_field_strength=self.vector_field_strength,
            vector_field_tightness=self.vector_field_tightness,
            texture_vector_field=self.texture_vector_field.name if self.texture_vector_field is not None else '',
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
            elif 'texture_vector_field' == attribute_name:
                texture_vector_field = resource_manager.get_texture(attribute_value)
                if texture_vector_field is not None:
                    self.texture_vector_field = texture_vector_field
            elif 'vector_field_position' == attribute_name:
                self.vector_field_position[...] = attribute_value
                self.update_vector_field_matrix()
            elif 'vector_field_rotation' == attribute_name:
                self.vector_field_rotation[...] = attribute_value
                self.update_vector_field_matrix()
            elif 'vector_field_scale' == attribute_name:
                self.vector_field_scale[...] = attribute_value
                self.update_vector_field_matrix()
            elif 'spawn_count' == attribute_name:
                self.set_spawn_count(attribute_value)
            elif 'cell_count' == attribute_name:
                self.cell_count[...] = [max(1, x) for x in attribute_value]
            else:
                setattr(self, attribute_name, attribute_value)
