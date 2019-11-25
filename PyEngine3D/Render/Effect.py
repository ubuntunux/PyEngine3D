from enum import Enum
import copy
import time
import math
import ctypes

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from PyEngine3D.Common import logger
from PyEngine3D.OpenGLContext import DispatchIndirectCommand, DispatchIndirectBuffer
from PyEngine3D.OpenGLContext import DrawElementsIndirectCommand, DrawElementIndirectBuffer
from PyEngine3D.OpenGLContext import ShaderStorageBuffer, InstanceBuffer, UniformBlock
from PyEngine3D.Utilities import *
from PyEngine3D.Common.Constants import *
from PyEngine3D.Common import logger, log_level, COMMAND
from PyEngine3D.App import CoreManager
from . import Model, BlendMode
from .RenderTarget import RenderTargets


class SpawnVolume(Enum):
    BOX = 0
    SPHERE = 1
    CONE = 2
    CYLINDER = 3


class VelocityType(Enum):
    RANDOM = 0
    SPAWN_DIRECTION = 1
    HURRICANE = 2


class AlignMode(Enum):
    NONE = 0
    BILLBOARD = 1
    VELOCITY_ALIGN = 2


class EffectManager(Singleton):
    def __init__(self):
        self.renderer = None
        self.effects = []
        self.active_effects = []
        self.render_effects = []
        self.resource_manager = None
        self.particle_instance_buffer = None
        self.alive_particle_count = 0
        self.test = 0

        self.material_gpu_particle_initialize = None
        self.material_gpu_particle_dispatch_indircet = None
        self.material_gpu_particle_spawn = None
        self.material_gpu_particle_update = None
        self.material_gpu_particle_draw_indirect = None
        self.material_gpu_particle_render = None

    def initialize(self, core_manager):
        self.renderer = core_manager.renderer
        self.resource_manager = core_manager.resource_manager

        self.particle_instance_buffer = InstanceBuffer(name="instance_buffer",
                                                       location_offset=5,
                                                       element_datas=[MATRIX4_IDENTITY,
                                                                      FLOAT4_ZERO,
                                                                      FLOAT4_ZERO])

        self.material_gpu_particle_initialize = self.resource_manager.get_material_instance('effect.gpu_particle_initialize')
        self.material_gpu_particle_dispatch_indircet = self.resource_manager.get_material_instance('effect.gpu_particle_dispatch_indirect')
        self.material_gpu_particle_spawn = self.resource_manager.get_material_instance('effect.gpu_particle_spawn')
        self.material_gpu_particle_update = self.resource_manager.get_material_instance('effect.gpu_particle_update')
        self.material_gpu_particle_draw_indirect = self.resource_manager.get_material_instance('effect.gpu_particle_draw_indirect')
        self.material_gpu_particle_render = self.resource_manager.get_material_instance('effect.gpu_particle_render')

    def get_save_data(self):
        return [effect.get_save_data() for effect in self.effects]

    def clear(self):
        for effect in self.effects:
            effect.destroy()

        self.effects = []
        self.active_effects = []

    def add_effect(self, effect):
        self.effects.append(effect)
        self.play_effect(effect)
        return effect

    def delete_effect(self, effect):
        self.destroy_effect(effect)
        self.effects.remove(effect)

    def play_effect(self, effect):
        if effect not in self.active_effects:
            self.active_effects.append(effect)
        effect.play()

    def destroy_effect(self, effect):
        if effect in self.active_effects:
            self.active_effects.remove(effect)
        effect.destroy()

    def notify_effect_info_changed(self, effect_info):
        for effect in self.effects:
            if effect_info == effect.effect_info:
                self.play_effect(effect)

    def notify_particle_info_changed(self, particle_info_name):
        for effect in self.effects:
            for emitter in effect.emitters:
                if particle_info_name == emitter.particle_info.name:
                    self.play_effect(effect)

    def render(self):
        prev_blend_mode = None
        main_camera = CoreManager.instance().scene_manager.main_camera
        cameara_position = main_camera.transform.get_pos()

        for effect in self.render_effects:
            for emitter in effect.emitters:
                particle_info = emitter.particle_info
                if not particle_info.enable or not emitter.alive:
                    continue

                # set blend mode
                if prev_blend_mode != particle_info.blend_mode:
                    if particle_info.blend_mode is BlendMode.BLEND:
                        glBlendEquation(GL_FUNC_ADD)
                        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                    elif particle_info.blend_mode is BlendMode.ADDITIVE:
                        glBlendEquation(GL_FUNC_ADD)
                        glBlendFunc(GL_ONE, GL_ONE)
                    elif particle_info.blend_mode is BlendMode.MULTIPLY:
                        glBlendEquation(GL_FUNC_ADD)
                        glBlendFunc(GL_ZERO, GL_SRC_COLOR)
                    elif particle_info.blend_mode is BlendMode.SUBTRACT:
                        glBlendEquation(GL_FUNC_SUBTRACT)
                        glBlendFunc(GL_ONE, GL_ONE)
                    prev_blend_mode = particle_info.blend_mode

                geometry = particle_info.mesh.get_geometry()

                # common
                uniform_data = self.renderer.uniform_particle_common_data
                uniform_data['PARTICLE_COLOR'] = particle_info.color
                uniform_data['PARTICLE_ALIGN_MODE'] = particle_info.align_mode.value
                uniform_data['PARTICLE_CELL_COUNT'] = particle_info.cell_count
                uniform_data['PARTICLE_BLEND_MODE'] = particle_info.blend_mode.value
                self.renderer.uniform_particle_common_buffer.bind_uniform_block(data=uniform_data)

                if particle_info.enable_gpu_particle:
                    uniform_data = self.renderer.uniform_particle_infos_data
                    uniform_data['PARTICLE_PARENT_MATRIX'] = effect.transform.matrix
                    uniform_data['PARTICLE_DELAY'] = particle_info.delay.value
                    uniform_data['PARTICLE_LIFE_TIME'] = particle_info.life_time.value
                    uniform_data['PARTICLE_MAX_COUNT'] = emitter.gpu_particle_max_count
                    uniform_data['PARTICLE_SPAWN_COUNT'] = emitter.gpu_particle_spawn_count
                    uniform_data['PARTICLE_FADE_IN'] = particle_info.fade_in
                    uniform_data['PARTICLE_FADE_OUT'] = particle_info.fade_out
                    uniform_data['PARTICLE_OPACITY'] = particle_info.opacity
                    uniform_data['PARTICLE_PLAY_SPEED'] = particle_info.play_speed
                    uniform_data['PARTICLE_FORCE_GRAVITY'] = particle_info.force_gravity
                    uniform_data['PARTICLE_FORCE_ELASTICITY'] = particle_info.force_elasticity
                    uniform_data['PARTICLE_FORCE_FRICTION'] = particle_info.force_friction
                    uniform_data['PARTICLE_TRANSFORM_ROTATION_MIN'] = particle_info.transform_rotation.value[0]
                    uniform_data['PARTICLE_TRANSFORM_ROTATION_MAX'] = particle_info.transform_rotation.value[1]
                    uniform_data['PARTICLE_TRANSFORM_SCALE_MIN'] = particle_info.transform_scale.value[0]
                    uniform_data['PARTICLE_TRANSFORM_SCALE_MAX'] = particle_info.transform_scale.value[1]
                    uniform_data['PARTICLE_VELOCITY_TYPE'] = particle_info.velocity_type.value
                    uniform_data['PARTICLE_VELOCITY_ACCELERATION'] = particle_info.velocity_acceleration
                    uniform_data['PARTICLE_VELOCITY_LIMIT'] = particle_info.velocity_limit.value
                    uniform_data['PARTICLE_VELOCITY_POSITION_MIN'] = particle_info.velocity_position.value[0]
                    uniform_data['PARTICLE_VELOCITY_POSITION_MAX'] = particle_info.velocity_position.value[1]
                    uniform_data['PARTICLE_VELOCITY_ROTATION_MIN'] = particle_info.velocity_rotation.value[0]
                    uniform_data['PARTICLE_VELOCITY_ROTATION_MAX'] = particle_info.velocity_rotation.value[1]
                    uniform_data['PARTICLE_VELOCITY_SCALE_MIN'] = particle_info.velocity_scale.value[0]
                    uniform_data['PARTICLE_VELOCITY_SCALE_MAX'] = particle_info.velocity_scale.value[1]
                    uniform_data['PARTICLE_VELOCITY_STRETCH'] = particle_info.velocity_stretch
                    uniform_data['PARTICLE_ENABLE_VECTOR_FIELD'] = particle_info.enable_vector_field
                    uniform_data['PARTICLE_VECTOR_FIELD_STRENGTH'] = particle_info.vector_field_strength
                    uniform_data['PARTICLE_VECTOR_FIELD_TIGHTNESS'] = particle_info.vector_field_tightness
                    uniform_data['PARTICLE_VECTOR_FIELD_MATRIX'] = emitter.vector_field_transform.matrix
                    uniform_data['PARTICLE_VECTOR_FIELD_INV_MATRIX'] = emitter.vector_field_transform.inverse_matrix
                    uniform_data['PARTICLE_SPAWN_VOLUME_INFO'] = particle_info.spawn_volume_info

                    spawn_volume_abs_axis_flag = (1 << 8) if particle_info.spawn_volume_abs_axis[0] else 0
                    spawn_volume_abs_axis_flag |= (1 << 9) if particle_info.spawn_volume_abs_axis[1] else 0
                    spawn_volume_abs_axis_flag |= (1 << 10) if particle_info.spawn_volume_abs_axis[2] else 0
                    uniform_data['PARTICLE_SPAWN_VOLUME_TYPE'] = particle_info.spawn_volume_type.value | spawn_volume_abs_axis_flag

                    uniform_data['PARTICLE_SPAWN_VOLUME_MATRIX'] = particle_info.spawn_volume_transform.matrix

                    self.renderer.uniform_particle_infos_buffer.bind_uniform_block(data=uniform_data)

                    # spawn gpu particle
                    if 0 < emitter.gpu_particle_spawn_count:
                        material_instance = self.material_gpu_particle_spawn
                        material_instance.use_program()
                        emitter.index_range_buffer.bind_buffer_base(0)
                        emitter.particle_buffer.bind_buffer_base(1)

                        dispatch_count = int((emitter.gpu_particle_spawn_count + WORK_GROUP_SIZE - 1) / WORK_GROUP_SIZE)
                        glDispatchCompute(dispatch_count, 1, 1)
                        glMemoryBarrier(GL_ALL_BARRIER_BITS)

                        # reset spawn count
                        emitter.gpu_particle_spawn_count = 0

                    # set dispatch indirect
                    material_instance = self.material_gpu_particle_dispatch_indircet
                    material_instance.use_program()
                    emitter.index_range_buffer.bind_buffer_base(0)
                    emitter.dispatch_indirect_buffer.bind_buffer_base(1)
                    glDispatchCompute(1, 1, 1)
                    glMemoryBarrier(GL_ALL_BARRIER_BITS)

                    # update gpu particle
                    material_instance = self.material_gpu_particle_update
                    material_instance.use_program()

                    if particle_info.enable_vector_field:
                        material_instance.bind_uniform_data('texture_vector_field', particle_info.texture_vector_field, wrap=GL_REPEAT)

                    if 0.0 != particle_info.force_elasticity or 0.0 != particle_info.force_friction:
                        material_instance.bind_uniform_data('texture_depth', RenderTargets.DEPTH)
                        material_instance.bind_uniform_data('texture_normal', RenderTargets.WORLD_NORMAL)

                    emitter.particle_buffer.bind_buffer_base(0)
                    emitter.index_range_buffer.bind_buffer_base(1)

                    emitter.dispatch_indirect_buffer.bind_buffer()
                    glDispatchComputeIndirect(0)
                    glMemoryBarrier(GL_ALL_BARRIER_BITS)

                    # set draw indirect
                    material_instance = self.material_gpu_particle_draw_indirect
                    material_instance.use_program()
                    emitter.index_range_buffer.bind_buffer_base(0)
                    emitter.draw_indirect_buffer.bind_buffer_base(1)

                    glDispatchCompute(1, 1, 1)
                    glMemoryBarrier(GL_ALL_BARRIER_BITS)

                    # render gpu particle
                    material_instance = self.material_gpu_particle_render
                    material_instance.use_program()
                    emitter.particle_buffer.bind_buffer_base(0)
                    emitter.index_range_buffer.bind_buffer_base(1)
                    material_instance.bind_uniform_data('texture_diffuse', particle_info.texture_diffuse)

                    emitter.draw_indirect_buffer.bind_buffer()
                    geometry.draw_elements_indirect()
                else:
                    # CPU Particle
                    material_instance = particle_info.material_instance
                    material_instance.use_program()
                    material_instance.bind_material_instance()
                    material_instance.bind_uniform_data('texture_diffuse', particle_info.texture_diffuse)

                    draw_count = 0
                    for particle in emitter.particles:
                        if particle.is_renderable():
                            if AlignMode.BILLBOARD == particle_info.align_mode:
                                particle_info.world_matrix_data[draw_count][...] = np.dot(particle.transform.matrix, main_camera.inv_view_origin)
                                particle_info.world_matrix_data[draw_count][3][...] = np.dot(particle.transform.matrix, particle.parent_matrix)[3]
                            elif AlignMode.VELOCITY_ALIGN == particle_info.align_mode:
                                world_velocity = np.dot(particle.velocity_position, particle.parent_matrix[0:3, 0:3])
                                velocity_length = length(world_velocity)
                                if 0.0 < velocity_length:
                                    direction = normalize(particle.parent_matrix[3][0:3] - cameara_position)
                                    world_velocity /= velocity_length
                                    world_matrix = particle_info.world_matrix_data[draw_count]
                                    world_matrix[0][0:3] = np.cross(world_velocity, direction)
                                    world_matrix[1][0:3] = world_velocity * (1.0 + velocity_length * particle_info.velocity_stretch * 0.1)
                                    world_matrix[2][0:3] = np.cross(world_matrix[0][0:3], world_velocity)
                                    world_matrix[3][...] = np.dot(particle.transform.matrix, particle.parent_matrix)[3]
                            else:
                                particle_info.world_matrix_data[draw_count][...] = np.dot(particle.transform.matrix, particle.parent_matrix)
                            particle_info.uvs_data[draw_count][0:2] = particle.sequence_uv
                            particle_info.uvs_data[draw_count][2:4] = particle.next_sequence_uv
                            particle_info.sequence_opacity_data[draw_count][0] = particle.sequence_ratio
                            particle_info.sequence_opacity_data[draw_count][1] = particle.final_opacity
                            draw_count += 1

                    if 0 < draw_count:
                        geometry.draw_elements_instanced(draw_count,
                                                         self.particle_instance_buffer,
                                                         [particle_info.world_matrix_data,
                                                          particle_info.uvs_data,
                                                          particle_info.sequence_opacity_data])

    @staticmethod
    def view_frustum_culling_effect(camera, effect):
        to_effect = effect.transform.pos - camera.transform.pos
        radius = effect.effect_info.radius * max(effect.transform.scale)
        for i in range(4):
            d = np.dot(camera.frustum_vectors[i], to_effect)
            if radius < d:
                return True
        return False

    def update(self, dt):
        main_camera = CoreManager.instance().scene_manager.main_camera
        self.render_effects = []
        self.alive_particle_count = 0

        for effect in self.active_effects:
            self.alive_particle_count += effect.update(dt)

            if effect.alive:
                if not self.view_frustum_culling_effect(main_camera, effect):
                    self.render_effects.append(effect)
            else:
                self.destroy_effect(effect)


class Effect:
    def __init__(self, **effect_data):
        self.name = effect_data.get('name', 'effect')
        self.effect_info = effect_data.get('effect_info')
        self.object_id = effect_data.get('object_id', 0)

        self.transform = TransformObject()
        self.transform.set_pos(effect_data.get('pos', (0.0, 0.0, 0.0)))
        self.transform.set_rotation(effect_data.get('rot', (0.0, 0.0, 0.0)))
        self.transform.set_scale(effect_data.get('scale', (1.0, 1.0, 1.0)))

        self.alive = False
        self.emitters = []
        self.attributes = Attributes()

    def get_save_data(self):
        save_data = dict(
            name=self.name,
            pos=self.transform.pos.tolist(),
            rot=self.transform.rot.tolist(),
            scale=self.transform.scale.tolist(),
            effect_info=self.effect_info.name if self.effect_info is not None else ''
        )
        return save_data

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)
        self.attributes.set_attribute('pos', self.transform.pos)
        self.attributes.set_attribute('rot', self.transform.rot)
        self.attributes.set_attribute('scale', self.transform.scale)
        self.attributes.set_attribute('effect_info', self.effect_info.name if self.effect_info is not None else '')
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        if attribute_name == 'pos':
            self.transform.set_pos(attribute_value)
        elif attribute_name == 'rot':
            self.transform.set_rotation(attribute_value)
        elif attribute_name == 'scale':
            self.transform.set_scale(attribute_value)

    def clear_effect(self):
        for emitter in self.emitters:
            emitter.destroy()

        self.emitters = []

    def play(self):
        if self.effect_info is None:
            return

        self.clear_effect()

        self.alive = True

        for particle_info in self.effect_info.particle_infos:
            emitter = Emitter(self, particle_info)
            self.emitters.append(emitter)

        for emitter in self.emitters:
            emitter.play()

    def destroy(self):
        self.alive = False
        self.clear_effect()

    def update(self, dt):
        if not self.alive:
            return

        self.transform.update_transform(update_inverse_matrix=True)

        is_alive = False
        alive_particle_count = 0

        for emitter in self.emitters:
            alive_particle_count += emitter.update(dt)
            is_alive = is_alive or emitter.alive

        if not is_alive:
            self.destroy()

        return alive_particle_count


class Emitter:
    particle_gpu_data_type = np.dtype([
        ('parent_matrix', np.float32, 16),
        ('local_matrix', np.float32, 16),
        ('force', np.float32, 3),
        ('delay', np.float32),
        ('transform_position', np.float32, 3),
        ('life_time', np.float32),
        ('transform_rotation', np.float32, 3),
        ('opacity', np.float32),
        ('transform_scale', np.float32, 3),
        ('elapsed_time', np.float32),
        ('velocity_position', np.float32, 3),
        ('sequence_ratio', np.float32),
        ('velocity_rotation', np.float32, 3),
        ('sequence_index', np.int32),
        ('velocity_scale', np.float32, 3),
        ('next_sequence_index', np.int32),
        ('sequence_uv', np.float32, 2),
        ('next_sequence_uv', np.float32, 2),
        ('relative_position', np.float32, 3),
        ('state', np.int32),
    ])

    index_range_data_type = np.dtype([('begin_index', np.uint32),
              ('instance_count', np.uint32),
              ('destroy_count', np.uint32),
              ('dummy', np.uint32)])

    def __init__(self, parent_effect, particle_info):
        self.parent_effect = parent_effect
        self.particle_info = particle_info

        self.alive = False
        self.elapsed_time = 0.0
        self.last_spawned_time = 0.0
        self.alive_particle_count = 0
        self.particles = []

        # gpu data
        self.need_to_initialize_gpu_buffer = True
        self.index_range_buffer = None
        self.dispatch_indirect_buffer = None
        self.draw_indirect_buffer = None
        self.particle_buffer = None
        self.gpu_particle_max_count = 0
        self.gpu_particle_spawn_count = 0

        self.has_vector_field_rotation = any([0.0 != x for x in particle_info.vector_field_rotation])
        self.vector_field_transform = TransformObject()
        self.reset_vector_field_transform()

    def reset_vector_field_transform(self):
        self.vector_field_transform.set_pos(self.particle_info.vector_field_position)
        self.vector_field_transform.set_rotation(self.particle_info.vector_field_rotation)
        self.vector_field_transform.set_scale(self.particle_info.vector_field_scale)
        self.vector_field_transform.update_transform(update_inverse_matrix=True)

    def create_gpu_buffer(self, count):
        self.delete_gpu_buffer()

        self.need_to_initialize_gpu_buffer = True

        self.gpu_particle_max_count = count

        index_range_data = np.zeros(1, self.index_range_data_type)

        self.index_range_buffer = ShaderStorageBuffer(name='index_range_buffer',
                                                      data_size=index_range_data.nbytes,
                                                      dtype=index_range_data.dtype,
                                                      init_data=index_range_data)

        dispatch_data = DispatchIndirectCommand(num_groups_x=count)
        self.dispatch_indirect_buffer = DispatchIndirectBuffer('indirect buffer',
                                                               data_size=dispatch_data.nbytes,
                                                               dtype=dispatch_data.dtype,
                                                               init_data=dispatch_data)

        draw_indirect_data = DrawElementsIndirectCommand(vertex_count=6, instance_count=count)
        self.draw_indirect_buffer = DrawElementIndirectBuffer('draw indirect buffer',
                                                              data_size=draw_indirect_data.nbytes,
                                                              dtype=draw_indirect_data.dtype,
                                                              init_data=draw_indirect_data)

        self.particle_buffer = ShaderStorageBuffer(name='particle_buffer',
                                                   data_size=self.particle_gpu_data_type.itemsize * count,
                                                   dtype=self.particle_gpu_data_type)

        self.particle_buffer.clear_buffer()

    def delete_gpu_buffer(self):
        if self.index_range_buffer is not None:
            self.index_range_buffer.delete()
            self.index_range_buffer = None

        if self.dispatch_indirect_buffer is not None:
            self.dispatch_indirect_buffer.delete()
            self.dispatch_indirect_buffer = None

        if self.draw_indirect_buffer is not None:
            self.draw_indirect_buffer.delete()
            self.draw_indirect_buffer = None

        if self.particle_buffer is not None:
            self.particle_buffer.delete()
            self.particle_buffer = None

    def is_infinite_emitter(self):
        return self.particle_info.spawn_end_time < 0.0

    def play(self):
        if not self.particle_info.enable:
            return

        self.destroy()

        self.alive = True
        self.elapsed_time = 0.0
        self.last_spawned_time = 0.0
        self.alive_particle_count = 0
        self.gpu_particle_spawn_count = 0

        if self.has_vector_field_rotation:
            self.reset_vector_field_transform()

        # pre-allocate particles and spawn at first time.
        if self.particle_info.enable_gpu_particle:
            # GPU Particle - create only one particle
            self.create_gpu_buffer(self.particle_info.max_particle_count)
            particle = Particle(self.parent_effect, self, self.particle_info)
            self.particles = [particle, ]
            # spawn only one particle for gpu particle
            self.spawn_particle(1)
            # spawn at first time
            # self.gpu_particle_spawn_count = self.particle_info.spawn_count
        else:
            # CPU Particle
            self.particles = [Particle(self.parent_effect, self, self.particle_info) for i in range(self.particle_info.max_particle_count)]
            # spawn at first time
            # self.spawn_particle(self.particle_info.spawn_count)

    def spawn_particle(self, spawn_count):
        spawn_count = min(spawn_count, self.particle_info.max_particle_count - self.alive_particle_count)
        if 0 < spawn_count:
            begin_index = self.alive_particle_count
            for i in range(spawn_count):
                self.particles[begin_index + i].spawn()
            self.alive_particle_count += spawn_count

    def destroy(self):
        self.alive = False

        for particle in self.particles:
            particle.destroy()

        self.particles = []

    def update(self, dt):
        if not self.alive or not self.particle_info.enable:
            return 0

        self.elapsed_time += dt

        # update particles
        index = 0
        alive_count = self.alive_particle_count
        for n in range(alive_count):
            particle = self.particles[index]
            particle.update(dt)

            if not particle.alive:
                self.alive_particle_count -= 1
                last_particle_index = self.alive_particle_count
                if 0 < self.alive_particle_count:
                    # swap the present and the last.
                    if index != last_particle_index:
                        self.particles[index] = self.particles[last_particle_index]
                        self.particles[last_particle_index] = particle
                        continue
            index += 1

        if self.has_vector_field_rotation:
            self.vector_field_transform.rotation(self.particle_info.vector_field_rotation * dt)
            self.vector_field_transform.update_transform(update_inverse_matrix=True)

        # spawn particles
        if self.is_infinite_emitter() or self.elapsed_time < self.particle_info.spawn_end_time:
            spawn_count = 0

            if self.particle_info.spawn_term <= 0.0:
                # continuously spawn
                spawn_count = self.particle_info.spawn_count
                self.last_spawned_time = self.elapsed_time
            else:
                # Spawn particles at regular intervals.
                if self.particle_info.enable_gpu_particle:
                    available_spawn_count = self.particle_info.max_particle_count
                else:
                    available_spawn_count = self.particle_info.max_particle_count - self.alive_particle_count

                if 0 < available_spawn_count:
                    available_spawn_number_of_times = int(available_spawn_count / self.particle_info.spawn_count)
                    spawn_number_of_times = int((self.elapsed_time - self.last_spawned_time) / self.particle_info.spawn_term)
                    spawn_number_of_times = min(spawn_number_of_times, available_spawn_number_of_times)
                    if 0 < spawn_number_of_times:
                        self.last_spawned_time = int(self.elapsed_time / self.particle_info.spawn_term) * self.particle_info.spawn_term
                        spawn_count = self.particle_info.spawn_count * spawn_number_of_times

            if 0 < spawn_count:
                if self.particle_info.enable_gpu_particle:
                    self.gpu_particle_spawn_count += spawn_count
                else:
                    self.spawn_particle(spawn_count)

        if 0 == self.alive_particle_count and not self.is_infinite_emitter() and self.particle_info.spawn_end_time < self.elapsed_time:
            self.destroy()

        return self.gpu_particle_max_count if self.particle_info.enable_gpu_particle else self.alive_particle_count


class Particle:
    def __init__(self, parent_effect, parent_emitter, particle_info):
        self.parent_effect = parent_effect
        self.parent_emitter = parent_emitter
        self.particle_info = particle_info
        self.alive = False
        self.elapsed_time = 0.0

        # sequence
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

    def initialize(self):
        self.total_cell_count = self.particle_info.cell_count[0] * self.particle_info.cell_count[1]

        if self.particle_info.enable_gpu_particle:
            # GPU Particle
            self.delay = self.particle_info.delay.get_max()
            self.life_time = self.particle_info.life_time.get_max()
            if not self.parent_emitter.is_infinite_emitter():
                self.life_time += self.particle_info.spawn_end_time
        else:
            # CPU Particle
            self.delay = self.particle_info.delay.get_uniform()
            self.life_time = self.particle_info.life_time.get_uniform()

            random_factor = np.array([np.random.uniform() for i in range(4)], dtype=np.float32)
            spawn_volume_info = self.particle_info.spawn_volume_info
            if SpawnVolume.BOX == self.particle_info.spawn_volume_type:
                spawn_position = spawn_volume_info * (random_factor[0:3] - 0.5)
            elif SpawnVolume.SPHERE == self.particle_info.spawn_volume_type:
                vector = normalize(random_factor[0:3] - 0.5)
                spawn_position = vector * lerp(spawn_volume_info[1], spawn_volume_info[0], random_factor[3] * random_factor[3]) * 0.5
            elif SpawnVolume.CONE == self.particle_info.spawn_volume_type:
                vector = normalize(random_factor[0:2] - 0.5)
                ratio = random_factor[2] * random_factor[2]
                y = spawn_volume_info[2] * (ratio - 0.5)
                l = lerp(spawn_volume_info[1], spawn_volume_info[0], ratio) * sqrt(random_factor[3]) * 0.5
                x = l * vector[0]
                z = l * vector[1]
                spawn_position = Float3(x, y, z)
            elif SpawnVolume.CYLINDER == self.particle_info.spawn_volume_type:
                vector = normalize(random_factor[0:2] - 0.5)
                y = spawn_volume_info[2] * (random_factor[2] - 0.5)
                l = lerp(spawn_volume_info[1], spawn_volume_info[0], random_factor[2] * random_factor[2]) * 0.5
                x = l * vector[0]
                z = l * vector[1]
                spawn_position = Float3(x, y, z)

            for i, is_abs_axis in enumerate(self.particle_info.spawn_volume_abs_axis):
                if is_abs_axis:
                    spawn_position[i] = abs(spawn_position[i])

            spawn_position[...] = np.dot([spawn_position[0], spawn_position[1], spawn_position[2], 1.0], self.particle_info.spawn_volume_transform.matrix)[:3]

            self.transform.set_pos(spawn_position)
            self.transform.set_rotation(self.particle_info.transform_rotation.get_uniform())
            self.transform.set_scale(self.particle_info.transform_scale.get_uniform())

            # Store metrics at the time of spawn.
            self.parent_matrix[...] = self.parent_effect.transform.matrix

            # We will apply inverse_matrix here because we will apply parent_matrix later.
            self.force[...] = np.dot([0.0, -self.particle_info.force_gravity, 0.0], self.parent_effect.transform.inverse_matrix[0:3, 0:3])

            self.velocity_position[...] = self.particle_info.velocity_position.get_uniform()
            if VelocityType.SPAWN_DIRECTION == self.particle_info.velocity_type:
                self.velocity_position[...] = abs(self.velocity_position) * normalize(spawn_position)
            elif VelocityType.HURRICANE == self.particle_info.velocity_type:
                self.velocity_position[...] = abs(self.velocity_position) * np.cross(WORLD_UP, normalize(spawn_position))

            self.velocity_rotation[...] = self.particle_info.velocity_rotation.get_uniform()
            self.velocity_scale[...] = self.particle_info.velocity_scale.get_uniform()

            self.has_velocity_position = any([v != 0.0 for v in self.velocity_position]) or self.particle_info.force_gravity != 0.0
            self.has_velocity_rotation = any([v != 0.0 for v in self.velocity_rotation])
            self.has_velocity_scale = any([v != 0.0 for v in self.velocity_scale])

            self.final_opacity = self.particle_info.opacity

    def spawn(self):
        self.initialize()

        self.alive = True
        self.elapsed_time = 0.0
        self.sequence_ratio = 0.0
        self.sequence_index = 0
        self.next_sequence_index = 0

    def destroy(self):
        self.alive = False

    def is_renderable(self):
        return self.alive and (self.delay <= 0.0)

    def is_infinite_particle(self):
        return self.particle_info.life_time.get_max() <= 0.0

    def update_sequence(self, life_ratio):
        if 1 < self.total_cell_count and 0 < self.particle_info.play_speed:
            ratio = life_ratio * self.particle_info.play_speed
            ratio = (self.total_cell_count - 1) * (ratio - math.floor(ratio))
            index = math.floor(ratio)
            next_index = min(index + 1, self.total_cell_count - 1)
            self.sequence_ratio = ratio - index

            if next_index == self.next_sequence_index:
                return

            cell_count = self.particle_info.cell_count
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
                self.elapsed_time += abs(self.delay)
                self.delay = 0.0
            else:
                return

        if self.life_time < self.elapsed_time:
            self.destroy()
            return

        life_ratio = 0.0
        if 0.0 < self.life_time:
            life_ratio = min(1.0, self.elapsed_time / self.life_time)

        left_life_time = self.life_time - self.elapsed_time

        self.elapsed_time += dt

        if self.particle_info.enable_gpu_particle:
            # gpu particle, just return.
            return

        self.update_sequence(life_ratio)

        # update transform
        if self.particle_info.force_gravity != 0.0:
            self.velocity_position += self.force * dt

        if self.has_velocity_position:
            if any(self.velocity_position != 0.0) and 0.0 != self.particle_info.velocity_acceleration:
                velocity_length = length(self.velocity_position)
                self.velocity_position /= velocity_length
                velocity_length += self.particle_info.velocity_acceleration * dt
                if 0.0 < self.particle_info.velocity_limit.value[1]:
                    velocity_length = min(velocity_length, self.particle_info.velocity_limit.value[1])
                velocity_length = max(velocity_length, self.particle_info.velocity_limit.value[0])
                self.velocity_position *= velocity_length

            self.transform.move(self.velocity_position * dt)

        if self.has_velocity_rotation:
            self.transform.rotation(self.velocity_rotation * dt)

        if self.has_velocity_scale:
            self.transform.scaling(self.velocity_scale * dt)

        self.transform.update_transform()

        if 0.0 != self.particle_info.fade_in or 0.0 != self.particle_info.fade_out:
            self.final_opacity = self.particle_info.opacity

            if 0.0 < self.particle_info.fade_in and self.life_time < self.particle_info.fade_in:
                self.final_opacity *= self.life_time / self.particle_info.fade_in

            if 0.0 < self.particle_info.fade_out and left_life_time < self.particle_info.fade_out:
                self.final_opacity *= left_life_time / self.particle_info.fade_out


class EffectInfo:
    def __init__(self, name, **effect_info):
        self.name = name
        self.radius = effect_info.get('radius', 1.0)
        self.particle_infos = effect_info.get('particle_infos', [])
        self.attributes = Attributes()

    def get_save_data(self):
        save_data = dict(radius=self.radius, particle_infos=[])

        for particle_info in self.particle_infos:
            save_data['particle_infos'].append(particle_info.name)
        return save_data

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)
        self.attributes.set_attribute('radius', self.radius)
        attributes = []
        for particle_info in self.particle_infos:
            attributes.append(particle_info.name)
        self.attributes.set_attribute('particle_infos', attributes)
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        if 'particle_infos' == attribute_name:
            resource_manager = CoreManager.instance().resource_manager
            particle_info = resource_manager.get_particle(attribute_value[attribute_index])
            if particle_info is not None:
                self.particle_infos[attribute_index] = particle_info
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)
        EffectManager.instance().notify_effect_info_changed(self)

    def add_particle_info(self):
        resource_manager = CoreManager.instance().resource_manager
        particle = resource_manager.get_default_particle()
        self.particle_infos.append(particle)
        EffectManager.instance().notify_effect_info_changed(self)

    def delete_particle_info(self, index):
        if index < len(self.particle_infos):
            self.particle_infos.pop(index)
        EffectManager.instance().notify_effect_info_changed(self)

    def refresh_attribute_info(self):
        CoreManager.instance().send(COMMAND.TRANS_RESOURCE_ATTRIBUTE, self.get_attribute())

    def add_component(self, attribute_name, parent_info, attribute_index):
        if 'particle_infos' == attribute_name:
            self.add_particle_info()
            self.refresh_attribute_info()

    def delete_component(self, attribute_name, parent_info, attribute_index):
        if parent_info is not None and 'particle_infos' == parent_info.attribute_name:
            self.delete_particle_info(attribute_index)
            self.refresh_attribute_info()


class ParticleInfo:
    def __init__(self, name, **particle_info):
        self.name = name
        self.blend_mode = BlendMode(particle_info.get('blend_mode', BlendMode.ADDITIVE.value))
        self.enable = particle_info.get('enable', True)
        self.enable_gpu_particle = particle_info.get('enable_gpu_particle', True)

        self.max_particle_count = particle_info.get('max_particle_count', 1)
        self.spawn_count = particle_info.get('spawn_count', 1)
        self.spawn_term = particle_info.get('spawn_term', 0.1)
        self.spawn_end_time = particle_info.get('spawn_end_time', -1.0)

        self.align_mode = AlignMode(particle_info.get('align_mode', AlignMode.BILLBOARD.value))
        self.color = particle_info.get('color', Float3(1.0, 1.0, 1.0))
        self.play_speed = particle_info.get('play_speed', 0.0)
        self.opacity = particle_info.get('opacity', 1.0)
        self.fade_in = particle_info.get('fade_in', 0.0)  # if 0.0 is none else curve
        self.fade_out = particle_info.get('fade_out', 0.0)

        resource_manager = CoreManager.instance().resource_manager
        default_mesh = resource_manager.get_default_mesh()
        default_material_instance = resource_manager.get_default_effect_material_instance()
        texture_white = resource_manager.get_texture('common.flat_white')

        self.mesh = particle_info.get('mesh') or default_mesh
        self.material_instance = particle_info.get('material_instance') or default_material_instance
        self.texture_diffuse = particle_info.get('texture_diffuse') or texture_white

        self.cell_count = np.array(particle_info.get('cell_count', [1, 1]), dtype=np.int32)

        self.delay = RangeVariable(**particle_info.get('delay', dict(min_value=0.0)))
        self.life_time = RangeVariable(**particle_info.get('life_time', dict(min_value=1.0)))

        self.spawn_volume_type = SpawnVolume(particle_info.get('spawn_volume_type', SpawnVolume.BOX.value))
        self.spawn_volume_info = particle_info.get('spawn_volume_info', Float3(1.0, 1.0, 1.0))
        self.spawn_volume_position = particle_info.get('spawn_volume_position', Float3())
        self.spawn_volume_rotation = particle_info.get('spawn_volume_rotation', Float3())
        self.spawn_volume_scale = particle_info.get('spawn_volume_scale', Float3(1.0, 1.0, 1.0))
        self.spawn_volume_abs_axis = particle_info.get('spawn_volume_abs_axis', [False, False, False])
        self.spawn_volume_transform = TransformObject()

        self.transform_rotation = RangeVariable(**particle_info.get('transform_rotation', dict(min_value=FLOAT3_ZERO)))
        self.transform_scale = RangeVariable(**particle_info.get('transform_scale', dict(min_value=Float3(1.0, 1.0, 1.0))))

        self.velocity_type = VelocityType(particle_info.get('velocity_type', VelocityType.SPAWN_DIRECTION.value))
        self.velocity_acceleration = particle_info.get('velocity_acceleration', 0.0)
        self.velocity_limit = RangeVariable(**particle_info.get('velocity_limit', dict(min_value=0.0)))
        self.velocity_position = RangeVariable(**particle_info.get('velocity_position', dict(min_value=FLOAT3_ZERO)))
        self.velocity_rotation = RangeVariable(**particle_info.get('velocity_rotation', dict(min_value=FLOAT3_ZERO)))
        self.velocity_scale = RangeVariable(**particle_info.get('velocity_scale', dict(min_value=FLOAT3_ZERO)))
        self.velocity_stretch = particle_info.get('velocity_stretch', 1.0)

        self.force_gravity = particle_info.get('force_gravity', 0.0)
        self.force_elasticity = particle_info.get('force_elasticity', 0.0)
        self.force_friction = particle_info.get('force_friction', 0.0)

        self.enable_vector_field = particle_info.get('enable_vector_field', False)
        texture_vector_field_name = particle_info.get('texture_vector_field', 'common.default_3d')
        self.texture_vector_field = resource_manager.get_texture_or_none(texture_vector_field_name)
        self.vector_field_strength = particle_info.get('vector_field_strength', 1.0)
        self.vector_field_tightness = particle_info.get('vector_field_tightness', 0.1)

        self.vector_field_position = particle_info.get('vector_field_position', Float3(0.0, 0.0, 0.0))
        self.vector_field_rotation = particle_info.get('vector_field_rotation', Float3(0.0, 0.0, 0.0))
        self.vector_field_scale = particle_info.get('vector_field_scale', Float3(1.0, 1.0, 1.0))

        self.attributes = Attributes()

        # instance buffer data
        self.world_matrix_data = None
        self.uvs_data = None
        self.sequence_opacity_data = None
        self.sequence_opacity_data = None

        self.refresh_spawn_count()

    def refresh_spawn_count(self):
        if self.spawn_term == 0.0:
            # emitte particles at once
            self.max_particle_count = self.spawn_count
        else:
            total_time = self.delay.get_max() + self.life_time.get_max()
            self.max_particle_count = self.spawn_count * math.ceil(float(total_time) / float(self.spawn_term)) + self.spawn_count

        # instance buffer data
        self.world_matrix_data = np.zeros(self.max_particle_count, dtype=(np.float32, (4, 4)))
        self.uvs_data = np.zeros(self.max_particle_count, dtype=(np.float32, 4))
        self.sequence_opacity_data = np.zeros(self.max_particle_count, dtype=(np.float32, 4))

    def update_spawn_volume_matrix(self):
        self.spawn_volume_transform.set_pos(self.spawn_volume_position)
        self.spawn_volume_transform.set_rotation(self.spawn_volume_rotation)
        self.spawn_volume_transform.set_scale(self.spawn_volume_scale)
        self.spawn_volume_transform.update_transform()

    def get_save_data(self):
        save_data = dict(
            enable=self.enable,
            blend_mode=self.blend_mode.value,
            spawn_count=self.spawn_count,
            spawn_term=self.spawn_term,
            spawn_end_time=self.spawn_end_time,
            align_mode=self.align_mode.value,
            velocity_stretch=self.velocity_stretch,
            color=self.color,
            enable_gpu_particle=self.enable_gpu_particle,
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instance=self.material_instance.name if self.material_instance is not None else '',
            texture_diffuse=self.texture_diffuse.name if self.texture_diffuse is not None else '',
            play_speed=self.play_speed,
            opacity=self.opacity,
            fade_in=self.fade_in,
            fade_out=self.fade_out,
            cell_count=self.cell_count.tolist(),
            delay=self.delay.get_save_data(),
            life_time=self.life_time.get_save_data(),
            spawn_volume_type=self.spawn_volume_type.value,
            spawn_volume_info=self.spawn_volume_info,
            spawn_volume_position=self.spawn_volume_position,
            spawn_volume_rotation=self.spawn_volume_rotation,
            spawn_volume_scale=self.spawn_volume_scale,
            spawn_volume_abs_axis=self.spawn_volume_abs_axis,
            transform_rotation=self.transform_rotation.get_save_data(),
            transform_scale=self.transform_scale.get_save_data(),
            velocity_type=self.velocity_type.value,
            velocity_acceleration=self.velocity_acceleration,
            velocity_limit=self.velocity_limit.get_save_data(),
            velocity_position=self.velocity_position.get_save_data(),
            velocity_rotation=self.velocity_rotation.get_save_data(),
            velocity_scale=self.velocity_scale.get_save_data(),
            force_gravity=self.force_gravity,
            force_elasticity=self.force_elasticity,
            force_friction=self.force_friction,
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
            if 'align_mode' == key:
                self.attributes.set_attribute(key, AlignMode(self.align_mode.value))
            elif 'blend_mode' == key:
                self.attributes.set_attribute(key, BlendMode(self.blend_mode.value))
            elif 'spawn_volume_type' == key:
                self.attributes.set_attribute(key, SpawnVolume(self.spawn_volume_type.value))
            elif 'velocity_type' == key:
                self.attributes.set_attribute(key, VelocityType(self.velocity_type.value))
            else:
                self.attributes.set_attribute(key, attributes[key])
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
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
            elif 'vector_field_rotation' == attribute_name:
                self.vector_field_rotation[...] = attribute_value
            elif 'vector_field_scale' == attribute_name:
                self.vector_field_scale[...] = attribute_value
            elif 'spawn_volume_position' == attribute_name:
                self.spawn_volume_position[...] = attribute_value
                self.update_spawn_volume_matrix()
            elif 'spawn_volume_rotation' == attribute_name:
                self.spawn_volume_rotation[...] = attribute_value
                self.update_spawn_volume_matrix()
            elif 'spawn_volume_scale' == attribute_name:
                self.spawn_volume_scale[...] = attribute_value
                self.update_spawn_volume_matrix()
            elif 'cell_count' == attribute_name:
                self.cell_count[...] = [max(1, x) for x in attribute_value]
            else:
                setattr(self, attribute_name, attribute_value)
        else:
            if 0 < len(item_info_history):
                particle_attribute_name = item_info_history[0].attribute_name
                if hasattr(self, particle_attribute_name):
                    particle_attribute = getattr(self, particle_attribute_name)
                    if isinstance(particle_attribute, RangeVariable):
                        if 'min_value' == attribute_name:
                            particle_attribute.set_range(attribute_value, particle_attribute.value[1])
                        elif 'max_value' == attribute_name:
                            particle_attribute.set_range(particle_attribute.value[0], attribute_value)
        self.notify_attribute_changed(attribute_name)
        EffectManager.instance().notify_particle_info_changed(self.name)

    def notify_attribute_changed(self, attribute_name):
        if attribute_name in ('delay', 'life_time', 'spawn_count', 'spawn_term', 'spawn_time'):
            self.refresh_spawn_count()
