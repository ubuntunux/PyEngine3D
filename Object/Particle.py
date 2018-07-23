import copy
import time
import math

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from Common import logger
from Object import TransformObject, Model
from OpenGLContext import InstanceBuffer, ShaderStorageBuffer, UniformBlock
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
        self.core_manager = None
        self.uniform_emitter_infos = None
        self.emitter_instance_buffer = None

        self.gpu_particle = None
        self.gpu_material_instance = False

    def initialize(self, core_manager):
        self.core_manager = core_manager
        self.uniform_emitter_infos = self.core_manager.renderer.uniform_emitter_infos

        self.emitter_instance_buffer = InstanceBuffer(name="instance_buffer",
                                                      location_offset=5,
                                                      element_datas=[MATRIX4_IDENTITY, FLOAT4_ZERO, FLOAT4_ZERO])
        self.gpu_particle = GPUParticle()

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
        if not self.gpu_material_instance:
            self.core_manager.scene_manager.add_particle(name='gpu_particle', particle_info='gpu_particle')
            self.gpu_material_instance = True

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

                if emitter_info.gpu_particle:
                    # GPU Particle
                    self.uniform_emitter_infos.bind_uniform_block(datas=[emitter_info.delay.value,
                                                                         emitter_info.life_time.value,
                                                                         emitter_info.velocity.value[0],
                                                                         emitter_info.gravity,
                                                                         emitter_info.velocity.value[1],
                                                                         emitter_info.opacity,
                                                                         emitter_info.position.value[0],
                                                                         0.0,
                                                                         emitter_info.position.value[1],
                                                                         0.0])
                    self.gpu_particle.render(emitter_info)
                else:
                    # CPU Particle
                    draw_count = 0
                    for emitter in particle.emitters_group[i]:
                        if emitter.is_renderable():
                            emitter_info.model_data[draw_count][...] = emitter.transform.matrix
                            emitter_info.uvs_data[draw_count][0:2] = emitter.sequence_uv
                            emitter_info.uvs_data[draw_count][2:4] = emitter.next_sequence_uv
                            emitter_info.sequence_opacity_data[draw_count][0] = emitter.sequence_ratio
                            emitter_info.sequence_opacity_data[draw_count][1] = emitter.final_opacity
                            draw_count += 1

                    if 0 < draw_count:
                        self.emitter_instance_buffer.bind_instance_buffer(datas=[emitter_info.model_data,
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


class GPUParticle:
    def __init__(self):
        resource_manager = CoreManager.instance().resource_manager
        self.mesh = resource_manager.get_default_mesh()
        self.material_instance = resource_manager.get_material_instance('fx.gpu_particle')
        self.gpu_update = resource_manager.get_material_instance('fx.gpu_update')

        self.data = np.zeros(100, dtype=[('delay', np.float32),
                                         ('life_time', np.float32),
                                         ('gravity', np.float32),
                                         ('opacity', np.float32),
                                         ('velocity', np.float32, 3),
                                         ('alive', np.int32),
                                         ('position', np.float32, 3),
                                         ('dummy_0', np.float32), ])

        self.buffer = ShaderStorageBuffer('emitter_buffer', 0, datas=[self.data])

    def render(self, emitter_info):
        self.gpu_update.use_program()
        self.buffer.bind_storage_buffer()
        glDispatchCompute(len(self.data), 1, 1)
        glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)

        glEnable(GL_BLEND)
        glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(GL_ONE, GL_ONE)

        self.material_instance.use_program()
        self.material_instance.bind_material_instance()
        self.buffer.bind_storage_buffer()
        self.material_instance.bind_uniform_data('particle_matrix', MATRIX4_IDENTITY)

        geometry = self.mesh.get_geometry()
        geometry.draw_elements_instanced(len(self.data))


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
        self.velocity[...] = self.emitter_info.velocity.get_value()
        self.rotation_velocity[...] = self.emitter_info.rotation_velocity.get_value()
        self.scale_velocity[...] = self.emitter_info.scale_velocity.get_value()

        self.transform.set_pos(self.emitter_info.position.get_value())
        self.transform.set_rotation(self.emitter_info.rotation.get_value())
        self.transform.set_scale(self.emitter_info.scale.get_value())

        self.has_velocity = any([v != 0.0 for v in self.velocity])
        self.has_rotation_velocity = any([v != 0.0 for v in self.rotation_velocity])
        self.has_scale_velocity = any([v != 0.0 for v in self.scale_velocity])
        self.final_opacity = self.emitter_info.opacity

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

        if 0.0 != self.emitter_info.gravity:
            self.velocity[1] -= self.emitter_info.gravity * dt

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
            self.final_opacity = (fade_in * (1.0 - life_ratio) + fade_out * life_ratio) * self.emitter_info.opacity


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
                        emitter_attribute.set_range(attribute_value, emitter_attribute.value[1])
                    elif 'max_value' == attribute_name:
                        emitter_attribute.set_range(emitter_attribute.value[0], attribute_value)
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
        self.play_speed = emitter_info.get('play_speed', 0.0)
        self.gravity = emitter_info.get('gravity', 0.0)
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

        # sequence
        self.loop = emitter_info.get('loop', -1)  # -1 is infinite
        self.cell_count = emitter_info.get('cell_count', [1, 1])

        # variance
        self.delay = RangeVariable(**emitter_info.get('delay', dict(min_value=0.0, max_value=0.0)))
        self.life_time = RangeVariable(**emitter_info.get('life_time', dict(min_value=1.0, max_value=5.0)))
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

        self.model_data = None
        self.uvs_data = None
        self.sequence_opacity_data = None

        self.attributes = Attributes()

        self.set_spawn_count(self.spawn_count)

    def set_spawn_count(self, spawn_count):
        self.spawn_count = spawn_count
        self.model_data = np.zeros(self.spawn_count, dtype=(np.float32, (4, 4)))
        self.uvs_data = np.zeros(self.spawn_count, dtype=(np.float32, 4))
        self.sequence_opacity_data = np.zeros(self.spawn_count, dtype=(np.float32, 4))

    def get_save_data(self):
        save_data = dict(
            enable=self.enable,
            blend_mode=self.blend_mode.value,
            spawn_count=self.spawn_count,
            billboard=self.billboard,
            color=self.color,
            gpu_particle=self.gpu_particle,
            mesh=self.mesh.name if self.mesh is not None else '',
            material_instance=self.material_instance.name if self.material_instance is not None else '',
            texture_diffuse=self.texture_diffuse.name if self.texture_diffuse is not None else '',
            play_speed=self.play_speed,
            gravity=self.gravity,
            opacity=self.opacity,
            fade_in=self.fade_in,
            fade_out=self.fade_out,
            loop=self.loop,
            cell_count=self.cell_count,
            delay=self.delay.get_save_data(),
            life_time=self.life_time.get_save_data(),
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
