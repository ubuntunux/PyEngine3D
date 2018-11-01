from enum import Enum
import copy
import time
import math
import ctypes

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from Common import logger
from Object import TransformObject, Model
from OpenGLContext import DispatchIndirectCommand, DispatchIndirectBuffer
from OpenGLContext import DrawElementsIndirectCommand, DrawElementIndirectBuffer
from OpenGLContext import ShaderStorageBuffer, InstanceBuffer, UniformBlock
from Utilities import *
from Common.Constants import *
from Common import logger, log_level, COMMAND
from App import CoreManager
from .RenderOptions import BlendMode



class SpawnVolume(Enum):
    POINT = 0
    BOX = 1
    SPHERE = 2
    CONE = 3
    CYLINDER = 4


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
                                                                      MATRIX4_IDENTITY,
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

    def render(self):
        prev_blend_mode = None

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
                        glBlendFunc(GL_DST_COLOR, GL_ZERO)
                    elif particle_info.blend_mode is BlendMode.MULTIPLY:
                        glBlendEquation(GL_FUNC_SUBTRACT)
                        glBlendFunc(GL_ONE, GL_ONE)
                    prev_blend_mode = particle_info.blend_mode

                geometry = particle_info.mesh.get_geometry()

                # common
                uniform_data = self.renderer.uniform_particle_common_data
                uniform_data['PARTICLE_COLOR'] = particle_info.color
                uniform_data['PARTICLE_BILLBOARD'] = particle_info.billboard
                uniform_data['PARTICLE_CELL_COUNT'] = particle_info.cell_count
                uniform_data['PARTICLE_BLEND_MODE'] = particle_info.blend_mode.value
                self.renderer.uniform_particle_common_buffer.bind_uniform_block(data=uniform_data)

                if particle_info.enable_gpu_particle:
                    # GPU Particle
                    uniform_data = self.renderer.uniform_particle_infos_data
                    uniform_data['PARTICLE_PARENT_MATRIX'] = effect.transform.matrix
                    uniform_data['PARTICLE_PARENT_INVERSE_MATRIX'] = effect.transform.inverse_matrix
                    uniform_data['PARTICLE_DELAY'] = particle_info.delay.value
                    uniform_data['PARTICLE_LIFE_TIME'] = particle_info.life_time.value
                    uniform_data['PARTICLE_TRANSFORM_POSITION_MIN'] = particle_info.transform_position.value[0]
                    uniform_data['PARTICLE_FORCE_GRAVITY'] = particle_info.force_gravity
                    uniform_data['PARTICLE_TRANSFORM_POSITION_MAX'] = particle_info.transform_position.value[1]
                    uniform_data['PARTICLE_FADE_IN'] = particle_info.fade_in
                    uniform_data['PARTICLE_TRANSFORM_ROTATION_MIN'] = particle_info.transform_rotation.value[0]
                    uniform_data['PARTICLE_FADE_OUT'] = particle_info.fade_out
                    uniform_data['PARTICLE_TRANSFORM_ROTATION_MAX'] = particle_info.transform_rotation.value[1]
                    uniform_data['PARTICLE_OPACITY'] = particle_info.opacity
                    uniform_data['PARTICLE_TRANSFORM_SCALE_MIN'] = particle_info.transform_scale.value[0]
                    uniform_data['PARTICLE_PLAY_SPEED'] = particle_info.play_speed
                    uniform_data['PARTICLE_TRANSFORM_SCALE_MAX'] = particle_info.transform_scale.value[1]
                    uniform_data['PARTICLE_VELOCITY_POSITION_MIN'] = particle_info.velocity_position.value[0]
                    uniform_data['PARTICLE_VELOCITY_POSITION_MAX'] = particle_info.velocity_position.value[1]
                    uniform_data['PARTICLE_VELOCITY_ROTATION_MIN'] = particle_info.velocity_rotation.value[0]
                    uniform_data['PARTICLE_VELOCITY_ROTATION_MAX'] = particle_info.velocity_rotation.value[1]
                    uniform_data['PARTICLE_VELOCITY_SCALE_MIN'] = particle_info.velocity_scale.value[0]
                    uniform_data['PARTICLE_VELOCITY_SCALE_MAX'] = particle_info.velocity_scale.value[1]
                    uniform_data['PARTICLE_ENABLE_VECTOR_FIELD'] = particle_info.enable_vector_field
                    uniform_data['PARTICLE_VECTOR_FIELD_STRENGTH'] = particle_info.vector_field_strength
                    uniform_data['PARTICLE_VECTOR_FIELD_TIGHTNESS'] = particle_info.vector_field_tightness
                    uniform_data['PARTICLE_VECTOR_FIELD_MATRIX'] = particle_info.vector_field_transform.matrix
                    uniform_data['PARTICLE_VECTOR_FIELD_INV_MATRIX'] = particle_info.vector_field_transform.inverse_matrix
                    uniform_data['PARTICLE_MAX_COUNT'] = emitter.gpu_particle_max_count
                    uniform_data['PARTICLE_SPAWN_COUNT'] = emitter.gpu_particle_spawn_count

                    self.renderer.uniform_particle_infos_buffer.bind_uniform_block(data=uniform_data)

                    # initialize gpu buffers
                    if emitter.need_to_initialize_gpu_buffer:
                        emitter.need_to_initialize_gpu_buffer = False
                        material_instance = self.material_gpu_particle_initialize
                        material_instance.use_program()

                        emitter.alive_particle_counter.bind_buffer_base(0)
                        emitter.update_particle_counter.bind_buffer_base(1)
                        emitter.particle_index_buffer.bind_buffer_base(2)

                        dispatchCount = int((emitter.gpu_particle_max_count + WORK_GROUP_SIZE - 1) / WORK_GROUP_SIZE)
                        glDispatchCompute(dispatchCount, 1, 1)
                        glMemoryBarrier(GL_COMMAND_BARRIER_BIT | GL_SHADER_STORAGE_BARRIER_BIT)

                    print("===========================================")

                    # spawn gpu particle
                    if 0 < emitter.gpu_particle_spawn_count:
                        material_instance = self.material_gpu_particle_spawn
                        material_instance.use_program()
                        emitter.alive_particle_counter.bind_buffer_base(0)
                        emitter.particle_index_buffer.bind_buffer_base(1)
                        emitter.particle_buffer.bind_buffer_base(2)

                        dispatchCount = int((emitter.gpu_particle_spawn_count + WORK_GROUP_SIZE - 1) / WORK_GROUP_SIZE)
                        glDispatchCompute(dispatchCount, 1, 1)
                        glMemoryBarrier(GL_COMMAND_BARRIER_BIT | GL_SHADER_STORAGE_BARRIER_BIT)
                        print("spawn :", emitter.gpu_particle_spawn_count)
                        print(" alive", emitter.alive_particle_counter.get_buffer_data())
                        print(" index", emitter.particle_index_buffer.get_buffer_data())
                        print(" states", emitter.particle_buffer.get_buffer_data()['state'])

                    # set dispatch indirect
                    material_instance = self.material_gpu_particle_dispatch_indircet
                    material_instance.use_program()
                    emitter.alive_particle_counter.bind_buffer_base(0)
                    emitter.update_particle_counter.bind_buffer_base(1)
                    emitter.dispatch_indirect_buffer.bind_buffer_base(2)

                    glDispatchCompute(1, 1, 1)
                    glMemoryBarrier(GL_COMMAND_BARRIER_BIT | GL_SHADER_STORAGE_BARRIER_BIT)

                    # update gpu particle
                    material_instance = self.material_gpu_particle_update
                    material_instance.use_program()

                    if particle_info.enable_vector_field:
                        material_instance.bind_uniform_data('texture_vector_field', particle_info.texture_vector_field)

                    emitter.particle_buffer.bind_buffer_base(0)
                    emitter.alive_particle_counter.bind_buffer_base(1)
                    emitter.update_particle_counter.bind_buffer_base(2)
                    emitter.particle_index_buffer.bind_buffer_base(3)

                    emitter.dispatch_indirect_buffer.bind_buffer()
                    glDispatchComputeIndirect(0)
                    glMemoryBarrier(GL_COMMAND_BARRIER_BIT | GL_SHADER_STORAGE_BARRIER_BIT)

                    print("update")
                    print(" alive", emitter.alive_particle_counter.get_buffer_data())
                    print(" update", emitter.update_particle_counter.get_buffer_data())
                    print(" index", emitter.particle_index_buffer.get_buffer_data())
                    print(" states", emitter.particle_buffer.get_buffer_data()['state'])

                    # set draw indirect
                    material_instance = self.material_gpu_particle_draw_indirect
                    material_instance.use_program()
                    emitter.update_particle_counter.bind_buffer_base(0)
                    emitter.draw_indirect_buffer.bind_buffer_base(1)

                    glDispatchCompute(1, 1, 1)
                    glMemoryBarrier(GL_COMMAND_BARRIER_BIT | GL_SHADER_STORAGE_BARRIER_BIT)

                    # render gpu particle
                    material_instance = self.material_gpu_particle_render
                    material_instance.use_program()
                    emitter.particle_buffer.bind_buffer_base(0)
                    emitter.particle_index_buffer.bind_buffer_base(1)
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
                            particle_info.parent_matrix_data[draw_count][...] = particle.parent_matrix
                            particle_info.matrix_data[draw_count][...] = particle.transform.matrix
                            particle_info.uvs_data[draw_count][0:2] = particle.sequence_uv
                            particle_info.uvs_data[draw_count][2:4] = particle.next_sequence_uv
                            particle_info.sequence_opacity_data[draw_count][0] = particle.sequence_ratio
                            particle_info.sequence_opacity_data[draw_count][1] = particle.final_opacity
                            draw_count += 1

                    if 0 < draw_count:
                        geometry.draw_elements_instanced(draw_count,
                                                         self.particle_instance_buffer,
                                                         [particle_info.parent_matrix_data,
                                                          particle_info.matrix_data,
                                                          particle_info.uvs_data,
                                                          particle_info.sequence_opacity_data])

    def view_frustum_culling_effect(self, camera, effect):
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

        for particle_info in self.effect_info.particle_infos:
            emitter = Emitter(self, particle_info)
            self.emitters.append(emitter)

        for emitter in self.emitters:
            emitter.play()

    def destroy(self):
        self.alive = False

        for emitter in self.emitters:
            emitter.destroy()

        self.emitters = []

    def update(self, dt):
        if not self.alive:
            return

        self.transform.update_transform(update_inverse_matrix=True)

        is_alive = self.alive
        alive_particle_count = 0

        for emitter in self.emitters:
            alive_particle_count += emitter.update(dt)
            is_alive = is_alive or emitter.alive

        if not is_alive:
            self.destroy()

        return alive_particle_count


class Emitter:
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
        self.alive_particle_counter = None
        self.particle_index_buffer = None
        self.update_particle_counter = None
        self.dispatch_indirect_buffer = None
        self.draw_indirect_buffer = None
        self.particle_buffer = None
        self.gpu_particle_max_count = 0
        self.gpu_particle_spawn_count = 0

    def create_gpu_buffer(self, count):
        self.delete_gpu_buffer()

        self.need_to_initialize_gpu_buffer = True

        self.gpu_particle_max_count = count

        self.alive_particle_counter = ShaderStorageBuffer(name='alive_particle_counter',
                                                               data_size=np.nbytes[np.uint32],
                                                               dtype=np.uint32)

        self.particle_index_buffer = ShaderStorageBuffer(name='particle_index_buffer',
                                                               data_size=np.nbytes[np.uint32] * count,
                                                               dtype=np.uint32)

        self.update_particle_counter = ShaderStorageBuffer(name='update_particle_counter',
                                                           data_size=np.nbytes[np.uint32],
                                                           dtype=np.uint32)

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

        particle_gpu_data_type = np.dtype([
            ('parent_matrix', np.float32, 16),
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
            ('state', np.int32),
            ('force', np.float32, 3), ('dummy_0', np.float32),
            ('transform_position', np.float32, 3), ('dummy_1', np.float32),
            ('transform_rotation', np.float32, 3), ('dummy_2', np.float32),
            ('transform_scale', np.float32, 3), ('dummy_3', np.float32),
            ('velocity_position', np.float32, 3), ('dummy_4', np.float32),
            ('velocity_rotation', np.float32, 3), ('dummy_5', np.float32),
            ('velocity_scale', np.float32, 3), ('dummy_6', np.float32)
        ])
        self.particle_buffer = ShaderStorageBuffer(name='particle_buffer',
                                                   data_size=particle_gpu_data_type.itemsize * count,
                                                   dtype=particle_gpu_data_type)

        self.particle_buffer.clear_buffer()

    def delete_gpu_buffer(self):
        if self.alive_particle_counter is not None:
            self.alive_particle_counter.delete()
            self.alive_particle_counter = None

        if self.particle_index_buffer is not None:
            self.particle_index_buffer.delete()
            self.particle_index_buffer = None

        if self.update_particle_counter is not None:
            self.update_particle_counter.delete()
            self.update_particle_counter = None

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
        self.destroy()

        self.alive = True
        self.elapsed_time = 0.0
        self.last_spawned_time = 0.0
        self.alive_particle_count = 0
        self.gpu_particle_spawn_count = 0

        particle_info = self.particle_info

        # pre-allocate particles and spawn at first time.
        if particle_info.enable_gpu_particle:
            # GPU Particle - create only one particle
            self.create_gpu_buffer(particle_info.max_particle_count)
            particle = Particle(self.parent_effect, self, particle_info)
            self.particles = [particle, ]
            # spawn only one particle for gpu particle
            self.spawn_particle(1)
        else:
            # CPU Particle
            self.particles = [Particle(self.parent_effect, self, particle_info) for i in range(particle_info.max_particle_count)]
            # spawn at first time
            self.spawn_particle(self.particle_info.spawn_count)

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
        if not self.alive:
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

        # spawn particles
        self.gpu_particle_spawn_count = 0

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
        else:
            # CPU Particle
            self.delay = self.particle_info.delay.get_uniform()
            self.life_time = self.particle_info.life_time.get_uniform()

            self.velocity_position[...] = self.particle_info.velocity_position.get_uniform()
            self.velocity_rotation[...] = self.particle_info.velocity_rotation.get_uniform()
            self.velocity_scale[...] = self.particle_info.velocity_scale.get_uniform()

            self.transform.set_pos(self.particle_info.transform_position.get_uniform())
            self.transform.set_rotation(self.particle_info.transform_rotation.get_uniform())
            self.transform.set_scale(self.particle_info.transform_scale.get_uniform())

            # Store metrics at the time of spawn.
            self.parent_matrix[...] = self.parent_effect.transform.matrix

            # We will apply inverse_matrix here because we will apply parent_matrix later.
            self.force[...] = np.dot([0.0, -self.particle_info.force_gravity, 0.0, 1.0],
                                     self.parent_effect.transform.inverse_matrix)[:3]

            self.has_velocity_position = \
                any([v != 0.0 for v in self.velocity_position]) or self.particle_info.force_gravity != 0.0
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

        self.elapsed_time += dt

        if self.life_time < self.elapsed_time:
            self.destroy()
            return

        if self.particle_info.enable_gpu_particle:
            # gpu particle, just return.
            return

        life_ratio = 0.0
        if 0.0 < self.life_time:
            life_ratio = min(1.0, self.elapsed_time / self.life_time)

        self.update_sequence(life_ratio)

        # update transform
        if self.particle_info.force_gravity != 0.0:
            self.velocity_position += self.force * dt

        if self.has_velocity_position:
            self.transform.move(self.velocity_position * dt)

        if self.has_velocity_rotation:
            self.transform.rotation(self.velocity_rotation * dt)

        if self.has_velocity_scale:
            self.transform.scaling(self.velocity_scale * dt)

        self.transform.update_transform()

        if 0.0 != self.particle_info.fade_in or 0.0 != self.particle_info.fade_out:
            self.final_opacity = self.particle_info.opacity

            left_life_time = self.life_time - self.elapsed_time

            if 0.0 < self.particle_info.fade_in and self.life_time < self.particle_info.fade_in:
                self.final_opacity *= self.life_time / self.particle_info.fade_in

            if 0.0 < self.particle_info.fade_out and left_life_time < self.particle_info.fade_out:
                self.final_opacity *= left_life_time / self.particle_info.fade_out


class EffectInfo:
    def __init__(self, name, **effect_info):
        self.name = name
        self.radius = effect_info.get('radius', 1.0)

        self.particle_infos = []

        for particle_info in effect_info.get('particle_infos', []):
            self.add_particle_info(**particle_info)

        self.attributes = Attributes()

    def add_particle_info(self, **particle_info):
        self.particle_infos.append(ParticleInfo(**particle_info))
        # refresh
        EffectManager.instance().notify_effect_info_changed(self)

    def delete_particle_info(self, index):
        if index < len(self.particle_infos):
            self.particle_infos.pop(index)
        # refresh
        EffectManager.instance().notify_effect_info_changed(self)

    def get_save_data(self):
        save_data = dict(radius=self.radius,
                         particle_infos=[])

        for particle_info in self.particle_infos:
            save_data['particle_infos'].append(particle_info.get_save_data())
        return save_data

    def get_attribute(self):
        self.attributes.set_attribute('name', self.name)
        self.attributes.set_attribute('radius', self.radius)
        attributes = []
        for particle_info in self.particle_infos:
            attributes.append(particle_info.get_attribute())
        self.attributes.set_attribute('particle_infos', attributes)
        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        item_info_history = []
        while parent_info is not None:
            item_info_history.insert(0, parent_info)
            parent_info = parent_info.parent_info

        if 1 < len(item_info_history) and 'particle_infos' == item_info_history[0].attribute_name:
            particle_index = item_info_history[1].index
            particle_info = self.particle_infos[particle_index]
            count = len(item_info_history)
            if 2 == count:
                particle_info.set_attribute(attribute_name, attribute_value, parent_info, attribute_index)
            else:
                particle_attribute_name = item_info_history[2].attribute_name
                if hasattr(particle_info, particle_attribute_name):
                    particle_attribute = getattr(particle_info, particle_attribute_name)
                    if type(particle_attribute) in (tuple, list, np.ndarray):
                        particle_info.set_attribute(attribute_name, attribute_value, parent_info, attribute_index)
                    elif isinstance(particle_attribute, RangeVariable):
                        if 'min_value' == attribute_name:
                            particle_attribute.set_range(attribute_value, particle_attribute.value[1])
                        elif 'max_value' == attribute_name:
                            particle_attribute.set_range(particle_attribute.value[0], attribute_value)
                    # notify
                    particle_info.notify_attribute_changed(particle_attribute_name)
                else:
                    particle_info.set_attribute(attribute_name, attribute_value, parent_info, attribute_index)
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)
        # refresh
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
    def __init__(self, **particle_info):
        self.particle_info = particle_info
        self.name = particle_info.get('name', 'Particle')
        self.blend_mode = BlendMode(particle_info.get('blend_mode', 0))
        self.enable = particle_info.get('enable', True)
        self.enable_gpu_particle = particle_info.get('enable_gpu_particle', True)

        self.max_particle_count = particle_info.get('max_particle_count', 1)
        self.spawn_count = particle_info.get('spawn_count', 1)
        self.spawn_term = particle_info.get('spawn_term', 0.1)
        self.spawn_end_time = particle_info.get('spawn_end_time', -1.0)

        self.billboard = particle_info.get('billboard', True)
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
        self.transform_position = RangeVariable(**particle_info.get('transform_position', dict(min_value=FLOAT3_ZERO)))
        self.transform_rotation = RangeVariable(**particle_info.get('transform_rotation', dict(min_value=FLOAT3_ZERO)))
        self.transform_scale = RangeVariable(
            **particle_info.get('transform_scale', dict(min_value=Float3(1.0, 1.0, 1.0))))
        self.velocity_position = RangeVariable(**particle_info.get('velocity_position', dict(min_value=FLOAT3_ZERO)))
        self.velocity_rotation = RangeVariable(**particle_info.get('velocity_rotation', dict(min_value=FLOAT3_ZERO)))
        self.velocity_scale = RangeVariable(**particle_info.get('velocity_scale', dict(min_value=FLOAT3_ZERO)))

        self.force_gravity = particle_info.get('force_gravity', 0.0)

        self.enable_vector_field = particle_info.get('enable_vector_field', False)
        texture_vector_field_name = particle_info.get('texture_vector_field', 'common.default_3d')
        self.texture_vector_field = resource_manager.get_texture_or_none(texture_vector_field_name)
        self.vector_field_strength = particle_info.get('vector_field_strength', 1.0)
        self.vector_field_tightness = particle_info.get('vector_field_tightness', 0.1)

        self.vector_field_position = particle_info.get('vector_field_position', Float3(0.0, 0.0, 0.0))
        self.vector_field_rotation = particle_info.get('vector_field_rotation', Float3(0.0, 0.0, 0.0))
        self.vector_field_scale = particle_info.get('vector_field_scale', Float3(1.0, 1.0, 1.0))
        self.vector_field_transform = TransformObject()
        self.update_vector_field_matrix()

        self.parent_matrix_data = None
        self.matrix_data = None
        self.uvs_data = None
        self.sequence_opacity_data = None

        self.attributes = Attributes()

        self.refresh_spawn_count()

    def refresh_spawn_count(self):
        if self.spawn_term == 0.0:
            # emitte particles at once
            self.max_particle_count = self.spawn_count
        else:
            total_time = self.delay.get_max() + self.life_time.get_max()
            self.max_particle_count = self.spawn_count * math.ceil(total_time / self.spawn_term)

        self.parent_matrix_data = np.zeros(self.max_particle_count, dtype=(np.float32, (4, 4)))
        self.matrix_data = np.zeros(self.max_particle_count, dtype=(np.float32, (4, 4)))
        self.uvs_data = np.zeros(self.max_particle_count, dtype=(np.float32, 4))
        self.sequence_opacity_data = np.zeros(self.max_particle_count, dtype=(np.float32, 4))

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
            spawn_term=self.spawn_term,
            spawn_end_time=self.spawn_end_time,
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
            elif 'cell_count' == attribute_name:
                self.cell_count[...] = [max(1, x) for x in attribute_value]
            else:
                setattr(self, attribute_name, attribute_value)

            self.notify_attribute_changed(attribute_name)

    def notify_attribute_changed(self, attribute_name):
        if attribute_name in ('delay', 'life_time', 'spawn_count', 'spawn_term', 'spawn_time'):
            self.refresh_spawn_count()
