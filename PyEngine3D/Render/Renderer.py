from ctypes import c_void_p
import math

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from PyEngine3D.Common import logger, COMMAND
from PyEngine3D.Common.Constants import *
from PyEngine3D.Utilities import *
from PyEngine3D.OpenGLContext import InstanceBuffer, FrameBufferManager, RenderBuffer, UniformBlock, CreateTexture
from .PostProcess import AntiAliasing, PostProcess
from . import RenderTargets, RenderOption, RenderingType, RenderGroup, RenderMode
from . import SkeletonActor, StaticActor, ScreenQuad, Line
from . import Spline3D


class Renderer(Singleton):
    def __init__(self):
        self.initialized = False
        self.view_mode = GL_FILL

        # managers
        self.core_manager = None
        self.viewport_manager = None
        self.resource_manager = None
        self.font_manager = None
        self.scene_manager = None
        self.debug_line_manager = None
        self.render_option_manager = None
        self.rendertarget_manager = None
        self.framebuffer_manager = None
        self.postprocess = None

        # components
        self.viewport = None
        self.debug_texture = None

        self.blend_enable = False
        self.blend_equation = GL_FUNC_ADD
        self.blend_func_src = GL_SRC_ALPHA
        self.blend_func_dst = GL_ONE_MINUS_SRC_ALPHA

        self.blend_enable_prev = self.blend_enable
        self.blend_equation_prev = self.blend_equation
        self.blend_func_src_prev = self.blend_func_src
        self.blend_func_dst_prev = self.blend_func_dst

        # scene constants uniform buffer
        self.uniform_scene_buffer = None
        self.uniform_scene_data = None
        self.uniform_view_buffer = None
        self.uniform_view_data = None
        self.uniform_view_projection_buffer = None
        self.uniform_view_projection_data = None
        self.uniform_light_buffer = None
        self.uniform_light_data = None
        self.uniform_point_light_buffer = None
        self.uniform_point_light_data = None
        self.uniform_particle_common_buffer = None
        self.uniform_particle_common_data = None
        self.uniform_particle_infos_buffer = None
        self.uniform_particle_infos_data = None

        # material instances
        self.scene_constants_material = None
        self.debug_bone_material = None
        self.shadowmap_material = None
        self.shadowmap_skeletal_material = None
        self.static_object_id_material = None
        self.skeletal_object_id_material = None
        self.selcted_static_object_material = None
        self.selcted_skeletal_object_material = None
        self.selcted_object_composite_material = None
        self.render_color_material = None
        self.render_heightmap_material = None

        # font
        self.font_instance_buffer = None
        self.font_shader = None

        self.actor_instance_buffer = None

        self.render_custom_translucent_callbacks = []

    def initialize(self, core_manager):
        logger.info("Initialize Renderer")
        self.core_manager = core_manager
        self.viewport_manager = core_manager.viewport_manager
        self.viewport = self.viewport_manager.main_viewport
        self.resource_manager = core_manager.resource_manager
        self.render_option_manager = core_manager.render_option_manager
        self.font_manager = core_manager.font_manager
        self.scene_manager = core_manager.scene_manager
        self.debug_line_manager = core_manager.debug_line_manager
        self.rendertarget_manager = core_manager.rendertarget_manager
        self.postprocess = PostProcess()
        self.postprocess.initialize()

        self.framebuffer_manager = FrameBufferManager.instance()

        # material instances
        self.scene_constants_material = self.resource_manager.get_material_instance('scene_constants_main')
        self.debug_bone_material = self.resource_manager.get_material_instance("debug_bone")
        self.shadowmap_material = self.resource_manager.get_material_instance("shadowmap")
        self.shadowmap_skeletal_material = self.resource_manager.get_material_instance(name="shadowmap_skeletal",
                                                                                       shader_name="shadowmap",
                                                                                       macros={"SKELETAL": 1})
        self.static_object_id_material = self.resource_manager.get_material_instance(name="render_static_object_id",
                                                                                     shader_name="render_object_id")
        self.skeletal_object_id_material = self.resource_manager.get_material_instance(name="render_skeletal_object_id",
                                                                                       shader_name="render_object_id",
                                                                                       macros={"SKELETAL": 1})
        self.selcted_static_object_material = self.resource_manager.get_material_instance("selected_object")
        self.selcted_skeletal_object_material = self.resource_manager.get_material_instance(name="selected_object_skeletal",
                                                                                            shader_name="selected_object",
                                                                                            macros={"SKELETAL": 1})
        self.selcted_object_composite_material = self.resource_manager.get_material_instance("selected_object_composite")
        self.render_color_material = self.resource_manager.get_material_instance(name="render_object_color", shader_name="render_object_color")
        self.render_heightmap_material = self.resource_manager.get_material_instance(name="render_heightmap", shader_name="render_heightmap")

        # font
        self.font_shader = self.resource_manager.get_material_instance("font")
        self.font_instance_buffer = InstanceBuffer(name="font_offset", location_offset=1, element_datas=[FLOAT4_ZERO, ])

        # instance buffer
        self.actor_instance_buffer = InstanceBuffer(name="actor_instance_buffer", location_offset=7, element_datas=[MATRIX4_IDENTITY, ])

        # scene constants uniform buffer
        program = self.scene_constants_material.get_program()

        self.uniform_scene_data = np.zeros(1, dtype=[('TIME', np.float32),
                                                     ('JITTER_FRAME', np.float32),
                                                     ('RENDER_SSR', np.int32),
                                                     ('RENDER_SSAO', np.int32),
                                                     ('SCREEN_SIZE', np.float32, 2),
                                                     ('BACKBUFFER_SIZE', np.float32, 2),
                                                     ('MOUSE_POS', np.float32, 2),
                                                     ('DELTA_TIME', np.float32),
                                                     ('SCENE_DUMMY_0', np.int32)])
        self.uniform_scene_buffer = UniformBlock("scene_constants", program, 0, self.uniform_scene_data)

        self.uniform_view_data = np.zeros(1, dtype=[('VIEW', np.float32, (4, 4)),
                                                    ('INV_VIEW', np.float32, (4, 4)),
                                                    ('VIEW_ORIGIN', np.float32, (4, 4)),
                                                    ('INV_VIEW_ORIGIN', np.float32, (4, 4)),
                                                    ('PROJECTION', np.float32, (4, 4)),
                                                    ('INV_PROJECTION', np.float32, (4, 4)),
                                                    ('CAMERA_POSITION', np.float32, 3),
                                                    ('VIEW_DUMMY_0', np.float32),
                                                    ('NEAR_FAR', np.float32, 2),
                                                    ('JITTER_DELTA', np.float32, 2),
                                                    ('JITTER_OFFSET', np.float32, 2),
                                                    ('VIEWCONSTANTS_DUMMY0', np.float32, 2)])
        self.uniform_view_buffer = UniformBlock("view_constants", program, 1, self.uniform_view_data)

        self.uniform_view_projection_data = np.zeros(1, dtype=[('VIEW_PROJECTION', np.float32, (4, 4)),
                                                               ('PREV_VIEW_PROJECTION', np.float32, (4, 4))])
        self.uniform_view_projection_buffer = UniformBlock("view_projection", program, 2,
                                                           self.uniform_view_projection_data)

        self.uniform_light_data = np.zeros(1, dtype=[('SHADOW_MATRIX', np.float32, (4, 4)),
                                                     ('LIGHT_POSITION', np.float32, 3),
                                                     ('SHADOW_EXP', np.float32),
                                                     ('LIGHT_DIRECTION', np.float32, 3),
                                                     ('SHADOW_BIAS', np.float32),
                                                     ('LIGHT_COLOR', np.float32, 3),
                                                     ('SHADOW_SAMPLES', np.int32)])
        self.uniform_light_buffer = UniformBlock("light_constants", program, 3, self.uniform_light_data)

        self.uniform_point_light_data = np.zeros(MAX_POINT_LIGHTS, dtype=[('color', np.float32, 3),
                                                                          ('radius', np.float32),
                                                                          ('pos', np.float32, 3),
                                                                          ('render', np.float32)])
        self.uniform_point_light_buffer = UniformBlock("point_light_constants", program, 4, self.uniform_point_light_data)

        self.uniform_particle_common_data = np.zeros(1, dtype=[
            ('PARTICLE_COLOR', np.float32, 3),
            ('PARTICLE_ALIGN_MODE', np.int32),
            ('PARTICLE_CELL_COUNT', np.int32, 2),
            ('PARTICLE_BLEND_MODE', np.int32),
            ('PARTICLE_COMMON_DUMMY_0', np.int32)
        ])
        self.uniform_particle_common_buffer = UniformBlock("particle_common", program, 5, self.uniform_particle_common_data)

        self.uniform_particle_infos_data = np.zeros(1, dtype=[
            ('PARTICLE_PARENT_MATRIX', np.float32, (4, 4)),
            ('PARTICLE_DELAY', np.float32, 2),
            ('PARTICLE_LIFE_TIME', np.float32, 2),
            ('PARTICLE_TRANSFORM_ROTATION_MIN', np.float32, 3),
            ('PARTICLE_FADE_IN', np.float32),
            ('PARTICLE_TRANSFORM_ROTATION_MAX', np.float32, 3),
            ('PARTICLE_FADE_OUT', np.float32),
            ('PARTICLE_TRANSFORM_SCALE_MIN', np.float32, 3),
            ('PARTICLE_OPACITY', np.float32),
            ('PARTICLE_TRANSFORM_SCALE_MAX', np.float32, 3),
            ('PARTICLE_ENABLE_VECTOR_FIELD', np.int32),
            ('PARTICLE_VELOCITY_POSITION_MIN', np.float32, 3),
            ('PARTICLE_VECTOR_FIELD_STRENGTH', np.float32),
            ('PARTICLE_VELOCITY_POSITION_MAX', np.float32, 3),
            ('PARTICLE_VECTOR_FIELD_TIGHTNESS', np.float32),
            ('PARTICLE_VELOCITY_ROTATION_MIN', np.float32, 3),
            ('PARTICLE_MAX_COUNT', np.uint32),
            ('PARTICLE_VELOCITY_ROTATION_MAX', np.float32, 3),
            ('PARTICLE_SPAWN_COUNT', np.uint32),
            ('PARTICLE_VELOCITY_SCALE_MIN', np.float32, 3),
            ('PARTICLE_VELOCITY_STRETCH', np.float32),
            ('PARTICLE_VELOCITY_SCALE_MAX', np.float32, 3),
            ('PARTICLE_VELOCITY_ACCELERATION', np.float32),
            ('PARTICLE_VECTOR_FIELD_MATRIX', np.float32, (4, 4)),
            ('PARTICLE_VECTOR_FIELD_INV_MATRIX', np.float32, (4, 4)),
            ('PARTICLE_SPAWN_VOLUME_INFO', np.float32, 3),
            ('PARTICLE_SPAWN_VOLUME_TYPE', np.uint32),
            ('PARTICLE_SPAWN_VOLUME_MATRIX', np.float32, (4, 4)),
            ('PARTICLE_VELOCITY_LIMIT', np.float32, 2),
            ('PARTICLE_FORCE_GRAVITY', np.float32),
            ('PARTICLE_PLAY_SPEED', np.float32),
            ('PARTICLE_VELOCITY_TYPE', np.uint32),
            ('PARTICLE_FORCE_ELASTICITY', np.float32),
            ('PARTICLE_FORCE_FRICTION', np.float32),
            ('PARTICLE_DUMMY_0', np.uint32),
        ])
        self.uniform_particle_infos_buffer = UniformBlock("particle_infos", program, 6, self.uniform_particle_infos_data)

        def get_rendering_type_name(rendering_type):
            rendering_type = str(rendering_type)
            return rendering_type.split('.')[-1] if '.' in rendering_type else rendering_type

        rendering_type_list = [get_rendering_type_name(RenderingType.convert_index_to_enum(x)) for x in range(RenderingType.COUNT.value)]

        self.initialized = True

        # Send to GUI
        self.core_manager.send_rendering_type_list(rendering_type_list)

    def close(self):
        pass

    def render_custom_translucent(self, render_custom_translucent_callback):
        self.render_custom_translucent_callbacks.append(render_custom_translucent_callback)

    def set_blend_state(self, blend_enable=True, equation=GL_FUNC_ADD, func_src=GL_SRC_ALPHA, func_dst=GL_ONE_MINUS_SRC_ALPHA):
        self.blend_enable_prev = self.blend_enable
        self.blend_equation_prev = self.blend_equation
        self.blend_func_src_prev = self.blend_func_src
        self.blend_func_dst_prev = self.blend_func_dst

        self.blend_enable = blend_enable
        if blend_enable:
            self.blend_equation = equation
            self.blend_func_src = func_src
            self.blend_func_dst = func_dst
            glEnable(GL_BLEND)
            glBlendEquation(equation)
            glBlendFunc(func_src, func_dst)
        else:
            glDisable(GL_BLEND)

    def restore_blend_state_prev(self):
        self.set_blend_state(self.blend_enable_prev,
                             self.blend_equation_prev,
                             self.blend_func_src_prev,
                             self.blend_func_dst_prev)

    def set_view_mode(self, view_mode):
        if view_mode == COMMAND.VIEWMODE_WIREFRAME:
            self.view_mode = GL_LINE
        elif view_mode == COMMAND.VIEWMODE_SHADING:
            self.view_mode = GL_FILL

    def reset_renderer(self):
        self.scene_manager.update_camera_projection_matrix(aspect=self.core_manager.game_backend.aspect)
        self.framebuffer_manager.clear_framebuffer()
        self.rendertarget_manager.create_rendertargets()
        self.scene_manager.reset_light_probe()
        self.core_manager.gc_collect()

    def ortho_view(self, look_at=True):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.viewport.width, 0, self.viewport.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        if look_at:
            self.look_at()

    def perspective_view(self, look_at=True):
        camera = self.scene_manager.main_camera

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(camera.fov, camera.aspect, camera.near, camera.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        if look_at:
            self.look_at()

    def look_at(self):
        camera = self.scene_manager.main_camera
        camera_target = -camera.transform.front
        camera_up = camera.transform.up

        glScalef(*(1.0 / camera.transform.get_scale()))
        gluLookAt(0.0, 0.0, 0.0, *camera_target, *camera_up)
        glTranslatef(*(-camera.transform.get_pos()))

    def set_debug_texture(self, texture):
        if texture is not None and texture is not RenderTargets.BACKBUFFER and type(texture) != RenderBuffer:
            self.debug_texture = texture
            self.postprocess.is_render_material_instance = False
            logger.info("Current texture : %s" % self.debug_texture.name)
        else:
            self.debug_texture = None

    def bind_uniform_blocks(self):
        camera = self.scene_manager.main_camera
        main_light = self.scene_manager.main_light

        if not camera or not main_light:
            return

        frame_count = self.core_manager.frame_count % 16

        uniform_data = self.uniform_scene_data
        uniform_data['TIME'] = self.core_manager.current_time
        uniform_data['JITTER_FRAME'] = frame_count
        uniform_data['RENDER_SSR'] = self.postprocess.is_render_ssr
        uniform_data['RENDER_SSAO'] = self.postprocess.is_render_ssao
        uniform_data['SCREEN_SIZE'] = (self.core_manager.game_backend.width, self.core_manager.game_backend.height)
        uniform_data['BACKBUFFER_SIZE'] = (RenderTargets.BACKBUFFER.width, RenderTargets.BACKBUFFER.height)
        uniform_data['MOUSE_POS'] = self.core_manager.get_mouse_pos()
        uniform_data['DELTA_TIME'] = self.core_manager.delta
        self.uniform_scene_buffer.bind_uniform_block(data=uniform_data)

        uniform_data = self.uniform_view_data
        uniform_data['VIEW'][...] = camera.view
        uniform_data['INV_VIEW'][...] = camera.inv_view
        uniform_data['VIEW_ORIGIN'][...] = camera.view_origin
        uniform_data['INV_VIEW_ORIGIN'][...] = camera.inv_view_origin
        uniform_data['PROJECTION'][...] = camera.projection_jitter
        uniform_data['INV_PROJECTION'][...] = camera.inv_projection_jitter
        uniform_data['CAMERA_POSITION'][...] = camera.transform.get_pos()
        uniform_data['NEAR_FAR'][...] = (camera.near, camera.far)
        uniform_data['JITTER_DELTA'][...] = self.postprocess.jitter_delta
        uniform_data['JITTER_OFFSET'][...] = self.postprocess.jitter
        self.uniform_view_buffer.bind_uniform_block(data=uniform_data)

        uniform_data = self.uniform_light_data
        uniform_data['SHADOW_MATRIX'][...] = main_light.shadow_view_projection
        uniform_data['SHADOW_EXP'] = main_light.shadow_exp
        uniform_data['SHADOW_BIAS'] = main_light.shadow_bias
        uniform_data['SHADOW_SAMPLES'] = main_light.shadow_samples
        uniform_data['LIGHT_POSITION'][...] = main_light.transform.get_pos()
        uniform_data['LIGHT_DIRECTION'][...] = main_light.transform.front
        uniform_data['LIGHT_COLOR'][...] = main_light.light_color[:3]
        self.uniform_light_buffer.bind_uniform_block(data=uniform_data)

        self.uniform_point_light_buffer.bind_uniform_block(data=self.uniform_point_light_data)

    def render_light_probe(self, light_probe):
        if light_probe.isRendered:
            return

        logger.info("Rendering Light Probe")

        # Set Valid
        light_probe.isRendered = True

        camera = self.scene_manager.main_camera

        old_pos = camera.transform.get_pos().copy()
        old_rot = camera.transform.get_rotation().copy()
        old_fov = camera.fov
        old_aspect = camera.aspect
        old_render_font = RenderOption.RENDER_FONT
        old_render_skeleton = RenderOption.RENDER_SKELETON_ACTOR
        old_render_effect = RenderOption.RENDER_EFFECT
        old_render_collision = RenderOption.RENDER_COLLISION

        old_render_ssr = self.postprocess.is_render_ssr
        old_render_motion_blur = self.postprocess.is_render_motion_blur
        old_antialiasing = self.postprocess.anti_aliasing
        old_debug_absolute = self.postprocess.debug_absolute
        old_debug_mipmap = self.postprocess.debug_mipmap
        old_debug_intensity_min = self.postprocess.debug_intensity_min
        old_debug_intensity_max = self.postprocess.debug_intensity_max

        # set render light probe
        RenderOption.RENDER_LIGHT_PROBE = True
        RenderOption.RENDER_SKELETON_ACTOR = False
        RenderOption.RENDER_EFFECT = False
        RenderOption.RENDER_FONT = False
        self.postprocess.is_render_motion_blur = False
        self.postprocess.anti_aliasing = AntiAliasing.NONE_AA

        camera.update_projection(fov=90.0, aspect=1.0)

        def render_cube_face(dst_texture, target_face, pos, rotation):
            camera.transform.set_pos(pos)
            camera.transform.set_rotation(rotation)
            camera.update(force_update=True)

            # render
            self.render_scene()

            # copy
            src_framebuffer = self.framebuffer_manager.get_framebuffer(RenderTargets.HDR)
            self.framebuffer_manager.bind_framebuffer(dst_texture, target_face=target_face)
            glClear(GL_COLOR_BUFFER_BIT)

            self.framebuffer_manager.mirror_framebuffer(src_framebuffer)

            return dst_texture

        target_faces = [GL_TEXTURE_CUBE_MAP_POSITIVE_X,
                        GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
                        GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
                        GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
                        GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
                        GL_TEXTURE_CUBE_MAP_NEGATIVE_Z]

        pos = light_probe.transform.get_pos()

        camera_rotations = [[0.0, math.pi * 1.5, 0.0],
                            [0.0, math.pi * 0.5, 0.0],
                            [math.pi * -0.5, math.pi * 1.0, 0.0],
                            [math.pi * 0.5, math.pi * 1.0, 0.0],
                            [0.0, math.pi * 1.0, 0.0],
                            [0.0, 0.0, 0.0]]

        # render atmosphere scene to light_probe textures.
        RenderOption.RENDER_ONLY_ATMOSPHERE = True
        texture_cube = RenderTargets.LIGHT_PROBE_ATMOSPHERE
        for i in range(6):
            render_cube_face(texture_cube, target_faces[i], pos, camera_rotations[i])
        texture_cube.generate_mipmap()

        # render final scene to temp textures.
        RenderOption.RENDER_ONLY_ATMOSPHERE = False
        texture_cube = light_probe.texture_probe
        for i in range(6):
            render_cube_face(texture_cube, target_faces[i], pos, camera_rotations[i])
        texture_cube.generate_mipmap()

        # convolution
        texture_info = light_probe.texture_probe.get_texture_info()
        texture_info['name'] = 'temp_cube'
        temp_cube = CreateTexture(**texture_info)
        mipmap_count = temp_cube.get_mipmap_count()

        face_matrixies = [np.array([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 1]], dtype=np.float32),
                          np.array([[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]], dtype=np.float32),
                          np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=np.float32),
                          np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=np.float32),
                          np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32),
                          np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]], dtype=np.float32)]

        convolve_environment = self.resource_manager.get_material_instance('convolve_environment')
        convolve_environment.use_program()

        for i in range(6):
            for lod in range(mipmap_count):
                self.framebuffer_manager.bind_framebuffer(temp_cube, target_face=target_faces[i], target_level=lod)
                glClear(GL_COLOR_BUFFER_BIT)
                convolve_environment.bind_uniform_data("texture_environment", texture_cube)
                convolve_environment.bind_uniform_data("face_matrix", face_matrixies[i])
                convolve_environment.bind_uniform_data("lod", float(lod))
                convolve_environment.bind_uniform_data("mipmap_count", float(mipmap_count))
                self.postprocess.draw_elements()

        light_probe.replace_texture_probe(temp_cube)

        self.rendertarget_manager.get_temporary('temp_cube', light_probe.texture_probe)

        RenderOption.RENDER_LIGHT_PROBE = False
        RenderOption.RENDER_SKELETON_ACTOR = old_render_skeleton
        RenderOption.RENDER_EFFECT = old_render_effect
        RenderOption.RENDER_FONT = old_render_font
        RenderOption.RENDER_COLLISION = old_render_collision

        self.postprocess.is_render_ssr = old_render_ssr
        self.postprocess.is_render_motion_blur = old_render_motion_blur
        self.postprocess.anti_aliasing = old_antialiasing
        self.postprocess.debug_absolute = old_debug_absolute
        self.postprocess.debug_mipmap = old_debug_mipmap
        self.postprocess.debug_intensity_min = old_debug_intensity_min
        self.postprocess.debug_intensity_max = old_debug_intensity_max

        camera.update_projection(old_fov, old_aspect)

        camera.transform.set_pos(old_pos)
        camera.transform.set_rotation(old_rot)
        camera.update(force_update=True)

    def render_gbuffer(self):
        self.framebuffer_manager.bind_framebuffer(RenderTargets.DIFFUSE,
                                                  RenderTargets.MATERIAL,
                                                  RenderTargets.WORLD_NORMAL,
                                                  depth_texture=RenderTargets.DEPTH)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # render terrain
        if self.scene_manager.terrain.is_render_terrain:
            self.scene_manager.terrain.render_terrain(RenderMode.GBUFFER)

        # render static actor
        if RenderOption.RENDER_STATIC_ACTOR:
            self.render_actors(RenderGroup.STATIC_ACTOR,
                               RenderMode.GBUFFER,
                               self.scene_manager.static_solid_render_infos)

        # render velocity
        self.framebuffer_manager.bind_framebuffer(RenderTargets.VELOCITY)
        glClear(GL_COLOR_BUFFER_BIT)

        if RenderOption.RENDER_STATIC_ACTOR:
            self.postprocess.render_velocity(RenderTargets.DEPTH)

        # render skeletal actor gbuffer
        if RenderOption.RENDER_SKELETON_ACTOR:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.DIFFUSE,
                                                      RenderTargets.MATERIAL,
                                                      RenderTargets.WORLD_NORMAL,
                                                      RenderTargets.VELOCITY,
                                                      depth_texture=RenderTargets.DEPTH)
            self.render_actors(RenderGroup.SKELETON_ACTOR,
                               RenderMode.GBUFFER,
                               self.scene_manager.skeleton_solid_render_infos)

    def render_shadow(self):
        light = self.scene_manager.main_light
        self.uniform_view_projection_data['VIEW_PROJECTION'][...] = light.shadow_view_projection
        self.uniform_view_projection_data['PREV_VIEW_PROJECTION'][...] = light.shadow_view_projection
        self.uniform_view_projection_buffer.bind_uniform_block(data=self.uniform_view_projection_data)

        # static shadow
        self.framebuffer_manager.bind_framebuffer(depth_texture=RenderTargets.STATIC_SHADOWMAP)
        glClear(GL_DEPTH_BUFFER_BIT)
        glFrontFace(GL_CCW)

        if self.scene_manager.terrain.is_render_terrain:
            self.scene_manager.terrain.render_terrain(RenderMode.SHADOW)

        if RenderOption.RENDER_STATIC_ACTOR:
            self.render_actors(RenderGroup.STATIC_ACTOR, RenderMode.SHADOW, self.scene_manager.static_shadow_render_infos, self.shadowmap_material)

        # dyanmic shadow
        self.framebuffer_manager.bind_framebuffer(depth_texture=RenderTargets.DYNAMIC_SHADOWMAP)
        glClear(GL_DEPTH_BUFFER_BIT)
        glFrontFace(GL_CCW)

        if RenderOption.RENDER_SKELETON_ACTOR:
            self.render_actors(RenderGroup.SKELETON_ACTOR, RenderMode.SHADOW, self.scene_manager.skeleton_shadow_render_infos, self.shadowmap_skeletal_material)

        # composite shadow maps
        self.framebuffer_manager.bind_framebuffer(RenderTargets.COMPOSITE_SHADOWMAP)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glDisable(GL_CULL_FACE)

        self.postprocess.render_composite_shadowmap(RenderTargets.STATIC_SHADOWMAP, RenderTargets.DYNAMIC_SHADOWMAP)

    def render_preprocess(self):
        # Linear depth
        self.framebuffer_manager.bind_framebuffer(RenderTargets.LINEAR_DEPTH)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.postprocess.render_linear_depth(RenderTargets.DEPTH, RenderTargets.LINEAR_DEPTH)

        # Screen Space Reflection
        if self.postprocess.is_render_ssr:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.SCREEN_SPACE_REFLECTION)
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_screen_space_reflection(RenderTargets.HDR,
                                                            RenderTargets.WORLD_NORMAL,
                                                            RenderTargets.MATERIAL,
                                                            RenderTargets.VELOCITY,
                                                            RenderTargets.LINEAR_DEPTH)

            # swap ssr resolve textures
            RenderTargets.SCREEN_SPACE_REFLECTION_RESOLVED, RenderTargets.SCREEN_SPACE_REFLECTION_RESOLVED_PREV = \
                RenderTargets.SCREEN_SPACE_REFLECTION_RESOLVED_PREV, RenderTargets.SCREEN_SPACE_REFLECTION_RESOLVED

            self.framebuffer_manager.bind_framebuffer(RenderTargets.SCREEN_SPACE_REFLECTION_RESOLVED)
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_screen_space_reflection_resolve(RenderTargets.SCREEN_SPACE_REFLECTION,
                                                                    RenderTargets.SCREEN_SPACE_REFLECTION_RESOLVED_PREV,
                                                                    RenderTargets.VELOCITY)

        # SSAO
        if self.postprocess.is_render_ssao:
            temp_ssao = self.rendertarget_manager.get_temporary('temp_ssao', RenderTargets.SSAO)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.SSAO)
            glClearColor(1.0, 1.0, 1.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_ssao(texture_size=(RenderTargets.SSAO.width, RenderTargets.SSAO.height),
                                         texture_lod=self.rendertarget_manager.texture_lod_in_ssao,
                                         texture_normal=RenderTargets.WORLD_NORMAL,
                                         texture_linear_depth=RenderTargets.LINEAR_DEPTH)
            self.postprocess.render_gaussian_blur(RenderTargets.SSAO, temp_ssao)

    def render_solid(self):
        if RenderingType.DEFERRED_RENDERING == self.render_option_manager.rendering_type:
            self.postprocess.render_deferred_shading(self.scene_manager.get_light_probe_texture(),
                                                     self.scene_manager.atmosphere)
        elif RenderingType.FORWARD_RENDERING == self.render_option_manager.rendering_type:
            self.render_actors(RenderGroup.STATIC_ACTOR,
                               RenderMode.FORWARD_SHADING,
                               self.scene_manager.static_solid_render_infos)
            self.render_actors(RenderGroup.SKELETON_ACTOR,
                               RenderMode.FORWARD_SHADING,
                               self.scene_manager.skeleton_solid_render_infos)

    def render_translucent(self):
        self.render_actors(RenderGroup.STATIC_ACTOR,
                           RenderMode.FORWARD_SHADING,
                           self.scene_manager.static_translucent_render_infos)
        self.render_actors(RenderGroup.SKELETON_ACTOR,
                           RenderMode.FORWARD_SHADING,
                           self.scene_manager.skeleton_translucent_render_infos)

        for render_custom_translucent_callback in self.render_custom_translucent_callbacks:
            render_custom_translucent_callback()
        self.render_custom_translucent_callbacks.clear()

    def render_effect(self):
        self.scene_manager.effect_manager.render()

    def render_actors(self, render_group, render_mode, render_infos, scene_material_instance=None):
        if len(render_infos) < 1:
            return

        last_actor = None
        last_actor_material = None
        last_actor_material_instance = None

        if scene_material_instance is not None:
            scene_material_instance.use_program()
            scene_material_instance.bind_material_instance()

        # render
        for render_info in render_infos:
            actor = render_info.actor
            geometry = render_info.geometry
            actor_material = render_info.material
            actor_material_instance = render_info.material_instance

            is_instancing = actor.is_instancing()

            if RenderMode.GBUFFER == render_mode or RenderMode.FORWARD_SHADING == render_mode:
                if last_actor_material != actor_material and actor_material is not None:
                    actor_material.use_program()

                if last_actor_material_instance != actor_material_instance and actor_material_instance is not None:
                    actor_material_instance.bind_material_instance()

                    actor_material_instance.bind_uniform_data('is_render_gbuffer', RenderMode.GBUFFER == render_mode)

                    if RenderMode.FORWARD_SHADING == render_mode:
                        actor_material_instance.bind_uniform_data('texture_probe', self.scene_manager.get_light_probe_texture())
                        actor_material_instance.bind_uniform_data('texture_shadow', RenderTargets.COMPOSITE_SHADOWMAP)
                        actor_material_instance.bind_uniform_data('texture_ssao', RenderTargets.SSAO)
                        actor_material_instance.bind_uniform_data('texture_scene_reflect', RenderTargets.SCREEN_SPACE_REFLECTION_RESOLVED)
                        # Bind Atmosphere
                        self.scene_manager.atmosphere.bind_precomputed_atmosphere(actor_material_instance)
            elif RenderMode.SHADOW == render_mode:
                if last_actor_material_instance != actor_material_instance and actor_material_instance is not None:
                    # get diffuse texture from actor material instance
                    data_diffuse = actor_material_instance.get_uniform_data('texture_diffuse')
                    scene_material_instance.bind_uniform_data('texture_diffuse', data_diffuse)

            if last_actor != actor:
                material_instance = scene_material_instance or actor_material_instance
                if RenderMode.OBJECT_ID == render_mode:
                    material_instance.bind_uniform_data('object_id', actor.get_object_id())
                elif RenderMode.GIZMO == render_mode:
                    material_instance.bind_uniform_data('color', actor.get_object_color())
                material_instance.bind_uniform_data('is_instancing', is_instancing)
                material_instance.bind_uniform_data('model', actor.transform.matrix)
                if render_group == RenderGroup.SKELETON_ACTOR:
                    animation_buffer = actor.get_animation_buffer(geometry.skeleton.index)
                    prev_animation_buffer = actor.get_prev_animation_buffer(geometry.skeleton.index)
                    material_instance.bind_uniform_data('bone_matrices', animation_buffer, num=len(animation_buffer))
                    material_instance.bind_uniform_data('prev_bone_matrices', prev_animation_buffer, num=len(prev_animation_buffer))
            # draw
            if is_instancing:
                geometry.draw_elements_instanced(actor.get_instance_render_count(), self.actor_instance_buffer, [actor.instance_matrix, ])
            else:
                geometry.draw_elements()

            last_actor = actor
            last_actor_material = actor_material
            last_actor_material_instance = actor_material_instance

    def render_selected_object(self):
        selected_object = self.scene_manager.get_selected_object()
        if selected_object is not None:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.TEMP_RGBA8)
            glDisable(GL_DEPTH_TEST)
            glDepthMask(False)
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT)
            self.set_blend_state(False)

            object_type = type(selected_object)
            if SkeletonActor == object_type and RenderOption.RENDER_SKELETON_ACTOR:
                self.render_actors(RenderGroup.SKELETON_ACTOR,
                                   RenderMode.SELECTED_OBJECT,
                                   self.scene_manager.selected_object_render_info,
                                   self.selcted_skeletal_object_material)
            elif StaticActor == object_type and RenderOption.RENDER_STATIC_ACTOR:
                self.render_actors(RenderGroup.STATIC_ACTOR,
                                   RenderMode.SELECTED_OBJECT,
                                   self.scene_manager.selected_object_render_info,
                                   self.selcted_static_object_material)
            elif Spline3D == object_type:
                self.debug_line_manager.bind_render_spline_program()
                self.debug_line_manager.render_spline(selected_object, Float4(1.0, 1.0, 1.0, 1.0))
            else:
                return

            # composite
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
            self.selcted_object_composite_material.use_program()
            self.selcted_object_composite_material.bind_uniform_data("texture_mask", RenderTargets.TEMP_RGBA8)
            self.postprocess.draw_elements()

    def render_axis_gizmo(self, render_mode):
        if self.scene_manager.get_selected_object() is not None:
            axis_gizmo_actor = self.scene_manager.get_axis_gizmo()
            material_instance = None
            if RenderMode.GIZMO == render_mode:
                material_instance = self.render_color_material
            elif RenderMode.OBJECT_ID == render_mode:
                material_instance = self.static_object_id_material
            material_instance.use_program()
            material_instance.bind_uniform_data('is_instancing', False)
            material_instance.bind_uniform_data('model', axis_gizmo_actor.transform.matrix)
            geometries = axis_gizmo_actor.get_geometries()
            for i, geometry in enumerate(geometries):
                if RenderMode.GIZMO == render_mode:
                    material_instance.bind_uniform_data('color', axis_gizmo_actor.get_object_color(i))
                elif RenderMode.OBJECT_ID == render_mode:
                    material_instance.bind_uniform_data('object_id', axis_gizmo_actor.get_object_id(i))
                geometry.draw_elements()

    def render_object_id(self):
        self.framebuffer_manager.bind_framebuffer(RenderTargets.OBJECT_ID, depth_texture=RenderTargets.OBJECT_ID_DEPTH)
        glDisable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(True)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.set_blend_state(False)

        # render static actor object id
        if RenderOption.RENDER_STATIC_ACTOR:
            self.render_actors(RenderGroup.STATIC_ACTOR,
                               RenderMode.OBJECT_ID,
                               self.scene_manager.static_solid_render_infos,
                               self.static_object_id_material)
            self.render_actors(RenderGroup.STATIC_ACTOR,
                               RenderMode.OBJECT_ID,
                               self.scene_manager.static_translucent_render_infos,
                               self.static_object_id_material)

        # render skeletal actor object id
        if RenderOption.RENDER_SKELETON_ACTOR:
            self.render_actors(RenderGroup.SKELETON_ACTOR,
                               RenderMode.OBJECT_ID,
                               self.scene_manager.skeleton_solid_render_infos,
                               self.skeletal_object_id_material)
            self.render_actors(RenderGroup.SKELETON_ACTOR,
                               RenderMode.OBJECT_ID,
                               self.scene_manager.skeleton_translucent_render_infos,
                               self.skeletal_object_id_material)

        # spline object id
        self.debug_line_manager.bind_render_spline_program()
        for spline in self.scene_manager.splines:
            object_id = spline.get_object_id()
            self.debug_line_manager.render_spline(spline, Float4(object_id, object_id, object_id, 1.0), add_width=10.0)

        # spline gizmo object id
        self.render_actors(RenderGroup.STATIC_ACTOR,
                           RenderMode.OBJECT_ID,
                           self.scene_manager.spline_gizmo_render_infos,
                           self.static_object_id_material)

        # gizmo object id
        glClear(GL_DEPTH_BUFFER_BIT)
        self.render_axis_gizmo(RenderMode.OBJECT_ID)

    def render_heightmap(self, actor):
        self.framebuffer_manager.bind_framebuffer(RenderTargets.TEMP_HEIGHT_MAP)
        self.set_blend_state(blend_enable=True, equation=GL_MAX, func_src=GL_ONE, func_dst=GL_ONE)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDisable(GL_CULL_FACE)
        glDisable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)

        self.render_heightmap_material.use_program()
        self.render_heightmap_material.bind_material_instance()
        self.render_heightmap_material.bind_uniform_data('model', actor.transform.matrix)
        self.render_heightmap_material.bind_uniform_data('bound_box_min', actor.bound_box.bound_min)
        self.render_heightmap_material.bind_uniform_data('bound_box_max', actor.bound_box.bound_max)
        actor.get_geometry(0).draw_elements()

        if RenderTargets.TEMP_HEIGHT_MAP.enable_mipmap:
            self.postprocess.render_generate_max_z(RenderTargets.TEMP_HEIGHT_MAP)

    def render_bones(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        mesh = self.resource_manager.get_mesh("Cube")
        static_actors = self.scene_manager.static_actors[:]

        if mesh and self.debug_bone_material:
            material_instance = self.debug_bone_material
            material_instance.use_program()
            material_instance.bind()

            def draw_bone(mesh, skeleton_mesh, parent_matrix, material_instance, bone, root_matrix, isAnimation):
                if isAnimation:
                    bone_transform = skeleton_mesh.get_animation_transform(bone.name, frame)
                else:
                    bone_transform = np.linalg.inv(bone.inv_bind_matrix)

                if bone.children:
                    for child_bone in bone.children:
                        if isAnimation:
                            bone_transform = skeleton_mesh.get_animation_transform(bone.name, frame)
                            child_transform = skeleton_mesh.get_animation_transform(child_bone.name, frame)
                        else:
                            bone_transform = np.linalg.inv(bone.inv_bind_matrix)
                            child_transform = np.linalg.inv(child_bone.inv_bind_matrix)
                        material_instance.bind_uniform_data("mat1", np.dot(bone_transform, root_matrix))
                        material_instance.bind_uniform_data("mat2", np.dot(child_transform, root_matrix))
                        mesh.draw_elements()
                        draw_bone(mesh, skeleton_mesh, bone_transform.copy(), material_instance, child_bone, root_matrix, isAnimation)
                else:
                    material_instance.bind_uniform_data("mat1", np.dot(bone_transform, root_matrix))
                    child_transform = np.dot(bone_transform, root_matrix)
                    child_transform[3, :] += child_transform[1, :]
                    material_instance.bind_uniform_data("mat2", child_transform)
                    mesh.draw_elements()

            for static_actor in static_actors:
                if static_actor.model and static_actor.model.mesh and static_actor.model.mesh.skeletons:
                    skeletons = static_actor.model.mesh.skeletons
                    skeleton_mesh = static_actor.model.mesh
                    frame_count = skeleton_mesh.get_animation_frame_count()
                    frame = math.fmod(self.core_manager.current_time * 30.0, frame_count) if frame_count > 0.0 else 0.0
                    isAnimation = frame_count > 0.0
                    for skeleton in skeletons:
                        matrix = static_actor.transform.matrix
                        for bone in skeleton.hierachy:
                            draw_bone(mesh, skeleton_mesh, Matrix4().copy(), material_instance, bone, matrix, isAnimation)

    def render_postprocess(self):
        # bind frame buffer
        self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)

        # copy HDR target
        src_framebuffer = self.framebuffer_manager.get_framebuffer(RenderTargets.HDR)
        self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR_TEMP)
        glClear(GL_COLOR_BUFFER_BIT)
        self.framebuffer_manager.copy_framebuffer(src_framebuffer)

        # Temporal AA
        if AntiAliasing.TAA == self.postprocess.anti_aliasing:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_temporal_antialiasing(RenderTargets.HDR_TEMP,
                                                          RenderTargets.TAA_RESOLVE,
                                                          RenderTargets.VELOCITY)

            src_framebuffer = self.framebuffer_manager.get_framebuffer(RenderTargets.HDR)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.TAA_RESOLVE)
            glClear(GL_COLOR_BUFFER_BIT)
            self.framebuffer_manager.copy_framebuffer(src_framebuffer)

        # Bloom
        if self.postprocess.is_render_bloom:
            self.postprocess.render_bloom(RenderTargets.HDR)

        # Light Shaft
        if self.postprocess.is_render_light_shaft:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.LIGHT_SHAFT)
            self.postprocess.render_light_shaft(RenderTargets.ATMOSPHERE, RenderTargets.DEPTH)

        # Depth Of Field
        if self.postprocess.is_render_depth_of_field:
            self.postprocess.render_depth_of_field()

        self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)

        RenderTargets.HDR.generate_mipmap()

        # Tone Map
        self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        glClear(GL_COLOR_BUFFER_BIT)
        self.postprocess.render_tone_map(RenderTargets.HDR,
                                         RenderTargets.BLOOM_0,
                                         RenderTargets.BLOOM_1,
                                         RenderTargets.BLOOM_2,
                                         RenderTargets.BLOOM_3,
                                         RenderTargets.BLOOM_4,
                                         RenderTargets.LIGHT_SHAFT)

        # MSAA Test
        if AntiAliasing.MSAA == self.postprocess.anti_aliasing:
            src_framebuffer = self.framebuffer_manager.get_framebuffer(RenderTargets.BACKBUFFER)
            glClear(GL_COLOR_BUFFER_BIT)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)
            # resolve MSAA
            self.framebuffer_manager.copy_framebuffer(src_framebuffer)

        # Motion Blur
        if self.postprocess.is_render_motion_blur:
            backbuffer_copy = self.rendertarget_manager.get_temporary('backbuffer_copy', RenderTargets.BACKBUFFER)
            self.framebuffer_manager.bind_framebuffer(backbuffer_copy)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_motion_blur(RenderTargets.VELOCITY, RenderTargets.BACKBUFFER)

            # copy to backbuffer
            src_framebuffer = self.framebuffer_manager.get_framebuffer(backbuffer_copy)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
            glClear(GL_COLOR_BUFFER_BIT)
            self.framebuffer_manager.copy_framebuffer(src_framebuffer)

    def render_log(self):
        self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        self.font_manager.render_log(self.viewport.width, self.viewport.height)

    def render_text(self, text_render_data, offset_x, offset_y, canvas_width, canvas_height):
        if 0 < text_render_data.render_count:
            self.font_shader.use_program()
            self.font_shader.bind_material_instance()
            self.font_shader.bind_uniform_data("texture_font", text_render_data.font_data.texture)
            self.font_shader.bind_uniform_data("font_size", text_render_data.font_size)
            self.font_shader.bind_uniform_data("offset", (offset_x, offset_y))
            self.font_shader.bind_uniform_data("inv_canvas_size", (1.0 / canvas_width, 1.0 / canvas_height))
            self.font_shader.bind_uniform_data("count_of_side", text_render_data.font_data.count_of_side)
            self.postprocess.draw_elements_instanced(text_render_data.render_count, self.font_instance_buffer, [text_render_data.render_queue, ])

    def render_axis(self):
        camera = self.scene_manager.main_camera
        line_thickness = 2.0
        line_length = 100.0
        line_size = Float2(line_length / self.core_manager.game_backend.width, line_length / self.core_manager.game_backend.height)
        line_offset = line_size - 1.0
        self.debug_line_manager.draw_debug_line_2d(line_offset, line_offset + camera.view_origin[2][0:2] * line_size, color=Float4(0.0, 0.0, 1.0, 1.0), width=line_thickness)
        self.debug_line_manager.draw_debug_line_2d(line_offset, line_offset + camera.view_origin[1][0:2] * line_size, color=Float4(0.0, 1.0, 0.0, 1.0), width=line_thickness)
        self.debug_line_manager.draw_debug_line_2d(line_offset, line_offset + camera.view_origin[0][0:2] * line_size, color=Float4(1.0, 0.0, 0.0, 1.0), width=line_thickness)

    def render_scene(self):
        main_camera = self.scene_manager.main_camera

        # bind scene constants uniform blocks
        self.bind_uniform_blocks()

        self.set_blend_state(False)

        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glPolygonMode(GL_FRONT_AND_BACK, self.view_mode)
        # glEnable(GL_FRAMEBUFFER_SRGB)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_TEXTURE_CUBE_MAP_SEAMLESS)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glFrontFace(GL_CCW)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(True)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        if self.postprocess.is_render_shader() and not RenderOption.RENDER_LIGHT_PROBE:
            """ debug shader """
            self.set_blend_state(False)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
            glClear(GL_COLOR_BUFFER_BIT)

            self.postprocess.render_material_instance()

        elif RenderOption.RENDER_ONLY_ATMOSPHERE and RenderOption.RENDER_LIGHT_PROBE:
            """ render light probe preprocess """
            self.framebuffer_manager.bind_framebuffer(RenderTargets.COMPOSITE_SHADOWMAP)
            glClearColor(1.0, 1.0, 1.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

            self.framebuffer_manager.bind_framebuffer(RenderTargets.WORLD_NORMAL, depth_texture=RenderTargets.DEPTH)
            glClearColor(0.0, 1.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            self.framebuffer_manager.bind_framebuffer(RenderTargets.LINEAR_DEPTH)
            glClearColor(1.0, 1.0, 1.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_linear_depth(RenderTargets.DEPTH, RenderTargets.LINEAR_DEPTH)

            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

            # render atmosphere
            if self.scene_manager.atmosphere.is_render_atmosphere:
                self.scene_manager.atmosphere.render_precomputed_atmosphere(RenderTargets.LINEAR_DEPTH,
                                                                            RenderTargets.COMPOSITE_SHADOWMAP,
                                                                            RenderOption.RENDER_LIGHT_PROBE)
            # done render light probe preprocess
            return
        else:
            """ render normal scene """
            self.scene_manager.ocean.simulateFFTWaves()

            # render gbuffer & preprocess
            camera = self.scene_manager.main_camera
            self.uniform_view_projection_data['VIEW_PROJECTION'][...] = camera.view_projection_jitter
            self.uniform_view_projection_data['PREV_VIEW_PROJECTION'][...] = camera.prev_view_projection_jitter
            self.uniform_view_projection_buffer.bind_uniform_block(data=self.uniform_view_projection_data)

            self.render_gbuffer()

            self.render_preprocess()

            self.render_shadow()

            # render solid
            camera = self.scene_manager.main_camera
            self.uniform_view_projection_data['VIEW_PROJECTION'][...] = camera.view_projection_jitter
            self.uniform_view_projection_data['PREV_VIEW_PROJECTION'][...] = camera.prev_view_projection_jitter
            self.uniform_view_projection_buffer.bind_uniform_block(data=self.uniform_view_projection_data)

            glFrontFace(GL_CCW)

            glDepthMask(False)  # cause depth prepass and gbuffer

            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR, depth_texture=RenderTargets.DEPTH)
            glClear(GL_COLOR_BUFFER_BIT)

            self.render_solid()

            # copy HDR Target
            src_framebuffer = self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)
            dst_framebuffer = self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR_TEMP)
            glClear(GL_COLOR_BUFFER_BIT)
            dst_framebuffer.copy_framebuffer(src_framebuffer)
            src_framebuffer.bind_framebuffer()

            # set common projection matrix
            camera = self.scene_manager.main_camera
            self.uniform_view_projection_data['VIEW_PROJECTION'][...] = camera.view_projection
            self.uniform_view_projection_data['PREV_VIEW_PROJECTION'][...] = camera.prev_view_projection
            self.uniform_view_projection_buffer.bind_uniform_block(data=self.uniform_view_projection_data)

            # render ocean
            if self.scene_manager.ocean.is_render_ocean:
                self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR, depth_texture=RenderTargets.DEPTH)
                glDisable(GL_CULL_FACE)
                glEnable(GL_DEPTH_TEST)
                glDepthMask(True)

                self.scene_manager.ocean.render_ocean(atmosphere=self.scene_manager.atmosphere,
                                                      texture_scene=RenderTargets.HDR_TEMP,
                                                      texture_linear_depth=RenderTargets.LINEAR_DEPTH,
                                                      texture_probe=RenderTargets.LIGHT_PROBE_ATMOSPHERE,
                                                      texture_shadow=RenderTargets.COMPOSITE_SHADOWMAP)

                # re copy Linear depth
                self.framebuffer_manager.bind_framebuffer(RenderTargets.LINEAR_DEPTH)
                self.postprocess.render_linear_depth(RenderTargets.DEPTH, RenderTargets.LINEAR_DEPTH)

            # render atmosphere
            if self.scene_manager.atmosphere.is_render_atmosphere:
                self.framebuffer_manager.bind_framebuffer(RenderTargets.ATMOSPHERE,
                                                          RenderTargets.ATMOSPHERE_INSCATTER)
                self.scene_manager.atmosphere.render_precomputed_atmosphere(RenderTargets.LINEAR_DEPTH,
                                                                            RenderTargets.COMPOSITE_SHADOWMAP,
                                                                            RenderOption.RENDER_LIGHT_PROBE)

            glEnable(GL_CULL_FACE)
            glEnable(GL_DEPTH_TEST)
            glDepthMask(False)

            # Composite Atmosphere
            if self.scene_manager.atmosphere.is_render_atmosphere:
                self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)

                self.set_blend_state(True, GL_FUNC_ADD, GL_ONE, GL_ONE_MINUS_SRC_ALPHA)

                composite_atmosphere = self.resource_manager.get_material_instance("precomputed_atmosphere.composite_atmosphere")
                composite_atmosphere.use_program()
                above_the_cloud = self.scene_manager.atmosphere.cloud_altitude < main_camera.transform.get_pos()[1]
                composite_atmosphere.bind_uniform_data("above_the_cloud", above_the_cloud)
                composite_atmosphere.bind_uniform_data("inscatter_power", self.scene_manager.atmosphere.inscatter_power)
                composite_atmosphere.bind_uniform_data("texture_atmosphere", RenderTargets.ATMOSPHERE)
                composite_atmosphere.bind_uniform_data("texture_inscatter", RenderTargets.ATMOSPHERE_INSCATTER)
                composite_atmosphere.bind_uniform_data("texture_linear_depth", RenderTargets.LINEAR_DEPTH)
                self.postprocess.draw_elements()

            # prepare translucent
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR, depth_texture=RenderTargets.DEPTH)
            glEnable(GL_DEPTH_TEST)

            # Translucent
            self.render_translucent()

            # render particle
            if RenderOption.RENDER_EFFECT:
                glDisable(GL_CULL_FACE)
                glEnable(GL_BLEND)

                self.render_effect()

                glDisable(GL_BLEND)
                glEnable(GL_CULL_FACE)

            # render probe done
            if RenderOption.RENDER_LIGHT_PROBE:
                return

            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

            self.set_blend_state(False)

            self.render_postprocess()

        if RenderOption.RENDER_OBJECT_ID:
            self.render_object_id()

        self.render_selected_object()

        # debug render target
        if self.debug_texture is not None:
            self.set_blend_state(False)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_texture(self.debug_texture)

        if RenderOption.RENDER_FONT:
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.render_log()

        if RenderOption.RENDER_DEBUG_LINE and self.debug_texture is None:
            # render world axis
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER, depth_texture=RenderTargets.DEPTH)
            self.render_axis()

            self.debug_line_manager.bind_render_spline_program()
            for spline in self.scene_manager.splines:
                self.debug_line_manager.render_spline(spline)

            self.debug_line_manager.render_debug_lines()

        if RenderOption.RENDER_GIZMO and self.debug_texture is None:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER, depth_texture=RenderTargets.DEPTH)
            glEnable(GL_DEPTH_TEST)
            glDepthMask(True)
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # render spline gizmo
            self.render_actors(RenderGroup.STATIC_ACTOR,
                               RenderMode.GIZMO,
                               self.scene_manager.spline_gizmo_render_infos,
                               self.render_color_material)

            # render transform axis gizmo
            glClear(GL_DEPTH_BUFFER_BIT)
            self.render_axis_gizmo(RenderMode.GIZMO)
