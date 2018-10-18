import os
import math
import platform as platformModule
import time as timeModule
import random


import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from PIL import Image

from Common import logger, log_level, COMMAND
from Common.Constants import *
from Utilities import *
from OpenGLContext import FrameBuffer, FrameBufferManager, RenderBuffer, UniformMatrix4, UniformBlock, CreateTexture
from OpenGLContext import OpenGLContext, InstanceBuffer
from Object.PostProcess import AntiAliasing, PostProcess
from Object.RenderTarget import RenderTargets
from Object.RenderOptions import RenderOption, RenderingType, RenderGroup, RenderMode
from Object.Actor import SkeletonActor, StaticActor


class DebugLine:
    def __init__(self, pos1, pos2, color=None, width=1.0):
        self.pos1 = pos1.copy()
        self.pos2 = pos2.copy()
        self.color = color.copy() if color is not None else [1.0, 1.0, 1.0]
        self.width = width


class Renderer(Singleton):
    def __init__(self):
        self.width = -1
        self.height = -1
        self.aspect = 0.0
        self.viewMode = GL_FILL

        # managers
        self.core_manager = None
        self.resource_manager = None
        self.font_manager = None
        self.scene_manager = None
        self.render_option_manager = None
        self.rendertarget_manager = None
        self.framebuffer_manager = None
        self.postprocess = None

        # components
        self.lastShader = None
        self.screen = None
        self.debug_texture = None

        self.blend_enable = False
        self.blend_equation = GL_FUNC_ADD
        self.blend_func_src = GL_SRC_ALPHA
        self.blend_func_dst = GL_ONE_MINUS_SRC_ALPHA

        self.blend_enable_prev = self.blend_enable
        self.blend_equation_prev = self.blend_equation
        self.blend_func_src_prev = self.blend_func_src
        self.blend_func_dst_prev = self.blend_func_dst

        self.actor_instance_buffer = None

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
        self.pre_pass_material = None
        self.pre_pass_skeletal_material = None
        self.shadowmap_material = None
        self.shadowmap_skeletal_material = None
        self.selcted_static_object_material = None
        self.selcted_skeletal_object_material = None
        self.selcted_object_composite_material = None

        self.debug_lines_2d = []
        self.debug_lines_3d = []

    def destroyScreen(self):
        self.core_manager.game_backend.quit()

    def initialize(self, core_manager):
        logger.info("Initialize Renderer")
        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.render_option_manager = core_manager.render_option_manager
        self.font_manager = core_manager.font_manager
        self.scene_manager = core_manager.scene_manager
        self.rendertarget_manager = core_manager.rendertarget_manager
        self.postprocess = PostProcess()
        self.postprocess.initialize()

        self.framebuffer_manager = FrameBufferManager.instance()

        # material instances
        self.scene_constants_material = self.resource_manager.get_default_material_instance()
        self.debug_bone_material = self.resource_manager.get_material_instance("debug_bone")
        self.pre_pass_material = self.resource_manager.get_material_instance("pre_pass")
        self.pre_pass_skeletal_material = self.resource_manager.get_material_instance(name="pre_pass_skeletal",
                                                                                      shader_name="pre_pass",
                                                                                      macros={"SKELETAL": 1})
        self.shadowmap_material = self.resource_manager.get_material_instance("shadowmap")
        self.shadowmap_skeletal_material = self.resource_manager.get_material_instance(name="shadowmap_skeletal",
                                                                                       shader_name="shadowmap",
                                                                                       macros={"SKELETAL": 1})

        self.selcted_static_object_material = self.resource_manager.get_material_instance("selected_object")
        self.selcted_skeletal_object_material = self.resource_manager.get_material_instance(
            name="selected_object_skeletal",
            shader_name="selected_object",
            macros={"SKELETAL": 1}
        )
        self.selcted_object_composite_material = self.resource_manager.get_material_instance(
            "selected_object_composite")

        # instance buffer
        self.actor_instance_buffer = InstanceBuffer(name="actor_instance_buffer",
                                                    location_offset=7,
                                                    element_datas=[MATRIX4_IDENTITY, ])

        # scene constants uniform buffer
        program = self.scene_constants_material.get_program()

        self.uniform_scene_data = np.zeros(1, dtype=[('TIME', np.float32),
                                                     ('JITTER_FRAME', np.float32),
                                                     ('RENDER_SSR', np.int32),
                                                     ('RENDER_SSAO', np.int32),
                                                     ('BACKBUFFER_SIZE', np.float32, 2),
                                                     ('MOUSE_POS', np.float32, 2),
                                                     ('SCENECONSTANTS_DUMMY_0', np.float32, 3),
                                                     ('DELTA_TIME', np.float32)])
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

        self.uniform_light_data = np.zeros(1, dtype=[('LIGHT_POSITION', np.float32, 3),
                                                     ('LIGHT_DUMMY_0', np.float32),
                                                     ('LIGHT_DIRECTION', np.float32, 3),
                                                     ('LIGHT_DUMMY_1', np.float32),
                                                     ('LIGHT_COLOR', np.float32, 4),
                                                     ('SHADOW_MATRIX', np.float32, (4, 4))])
        self.uniform_light_buffer = UniformBlock("light_constants", program, 3, self.uniform_light_data)

        self.uniform_point_light_data = np.zeros(MAX_POINT_LIGHTS, dtype=[('color', np.float32, 3),
                                                                          ('radius', np.float32, 1),
                                                                          ('pos', np.float32, 3),
                                                                          ('render', np.float32, 1)])
        self.uniform_point_light_buffer = UniformBlock("point_light_constants", program, 4,
                                                       self.uniform_point_light_data)

        self.uniform_particle_common_data = np.zeros(1, dtype=[
            ('PARTICLE_COLOR', np.float32, 3),
            ('PARTICLE_BILLBOARD', np.int32),
            ('PARTICLE_CELL_COUNT', np.int32, 2),
            ('PARTICLE_BLEND_MODE', np.int32),
            ('PARTICLE_COMMON_DUMMY_0', np.int32)
        ])
        self.uniform_particle_common_buffer = UniformBlock("particle_common", program, 5,
                                                           self.uniform_particle_common_data)

        self.uniform_particle_infos_data = np.zeros(1, dtype=[
            ('PARTICLE_PARENT_MATRIX', np.float32, (4, 4)),
            ('PARTICLE_PARENT_INVERSE_MATRIX', np.float32, (4, 4)),
            ('PARTICLE_DELAY', np.float32, 2),
            ('PARTICLE_LIFE_TIME', np.float32, 2),
            ('PARTICLE_TRANSFORM_POSITION_MIN', np.float32, 3),
            ('PARTICLE_FORCE_GRAVITY', np.float32),
            ('PARTICLE_TRANSFORM_POSITION_MAX', np.float32, 3),
            ('PARTICLE_FADE_IN', np.float32),
            ('PARTICLE_TRANSFORM_ROTATION_MIN', np.float32, 3),
            ('PARTICLE_FADE_OUT', np.float32),
            ('PARTICLE_TRANSFORM_ROTATION_MAX', np.float32, 3),
            ('PARTICLE_OPACITY', np.float32),
            ('PARTICLE_TRANSFORM_SCALE_MIN', np.float32, 3),
            ('PARTICLE_PLAY_SPEED', np.float32),
            ('PARTICLE_TRANSFORM_SCALE_MAX', np.float32, 3),
            ('PARTICLE_USE_ATOMIC_COUNTER', np.int32),
            ('PARTICLE_VELOCITY_POSITION_MIN', np.float32, 3),
            ('PARTICLE_ENABLE_VECTOR_FIELD', np.int32),
            ('PARTICLE_VELOCITY_POSITION_MAX', np.float32, 3),
            ('PARTICLE_VECTOR_FIELD_STRENGTH', np.float32),
            ('PARTICLE_VELOCITY_ROTATION_MIN', np.float32, 3),
            ('PARTICLE_VECTOR_FIELD_TIGHTNESS', np.float32),
            ('PARTICLE_VELOCITY_ROTATION_MAX', np.float32, 3),
            ('dummy_0', np.float32),
            ('PARTICLE_VELOCITY_SCALE_MIN', np.float32, 3),
            ('dummy_1', np.float32),
            ('PARTICLE_VELOCITY_SCALE_MAX', np.float32, 3),
            ('dummy_2', np.float32),
            ('PARTICLE_VECTOR_FIELD_MATRIX', np.float32, (4, 4)),
            ('PARTICLE_VECTOR_FIELD_INV_MATRIX', np.float32, (4, 4))
        ])
        self.uniform_particle_infos_buffer = UniformBlock("particle_infos", program, 6,
                                                          self.uniform_particle_infos_data)

        # set gl hint
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

        def get_rendering_type_name(rendering_type):
            rendering_type = str(rendering_type)
            return rendering_type.split('.')[-1] if '.' in rendering_type else rendering_type

        rendering_type_list = [get_rendering_type_name(RenderingType.convert_index_to_enum(x)) for x in
                               range(RenderingType.COUNT.value)]
        # Send to GUI
        self.core_manager.send_rendering_type_list(rendering_type_list)

    def close(self):
        pass

    def set_blend_state(self, blend_enable=True, equation=GL_FUNC_ADD, func_src=GL_SRC_ALPHA,
                        func_dst=GL_ONE_MINUS_SRC_ALPHA):
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

    def set_view_mode(self, viewMode):
        if viewMode == COMMAND.VIEWMODE_WIREFRAME:
            self.viewMode = GL_LINE
        elif viewMode == COMMAND.VIEWMODE_SHADING:
            self.viewMode = GL_FILL

    def resizeScene(self, width=0, height=0, clear_rendertarget=False):
        changed = False

        if 0 < width and width != self.width:
            self.width = width
            changed = True

        if 0 < height and height != self.height:
            self.height = height
            changed = True

        self.aspect = float(self.width) / float(self.height)

        # update perspective and ortho
        self.scene_manager.update_camera_projection_matrix(aspect=self.aspect)

        # recreate render targets and framebuffer
        if changed or clear_rendertarget:
            self.framebuffer_manager.clear_framebuffer()
            self.rendertarget_manager.create_rendertargets()
            self.scene_manager.reset_light_probe()
            if self.scene_manager.atmosphere:
                self.scene_manager.atmosphere.initialize()
        self.core_manager.gc_collect()

    def ortho_view(self, look_at=True):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        if look_at:
            self.look_at()

    def perspective_view(self, look_at=True):
        camera = self.scene_manager.main_camera

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(camera.fov, self.aspect, camera.near, camera.far)
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
        uniform_data['TIME'] = self.core_manager.currentTime
        uniform_data['JITTER_FRAME'] = frame_count
        uniform_data['RENDER_SSR'] = self.postprocess.is_render_ssr
        uniform_data['RENDER_SSAO'] = self.postprocess.is_render_ssao
        uniform_data['BACKBUFFER_SIZE'] = (RenderTargets.BACKBUFFER.width,
                                           RenderTargets.BACKBUFFER.height)
        uniform_data['MOUSE_POS'] = self.core_manager.get_mouse_pos()
        uniform_data['DELTA_TIME'] = self.core_manager.delta
        self.uniform_scene_buffer.bind_uniform_block(data=uniform_data)

        uniform_data = self.uniform_view_data
        uniform_data['VIEW'][...] = camera.view
        uniform_data['INV_VIEW'][...] = np.linalg.inv(camera.view)
        uniform_data['VIEW_ORIGIN'][...] = camera.view_origin
        uniform_data['INV_VIEW_ORIGIN'][...] = np.transpose(camera.view_origin)
        uniform_data['PROJECTION'][...] = camera.projection
        uniform_data['INV_PROJECTION'][...] = np.linalg.inv(camera.projection)
        uniform_data['CAMERA_POSITION'][...] = camera.transform.get_pos()
        uniform_data['NEAR_FAR'][...] = (camera.near, camera.far)
        uniform_data['JITTER_DELTA'][...] = self.postprocess.jitter_delta
        uniform_data['JITTER_OFFSET'][...] = self.postprocess.jitter
        self.uniform_view_buffer.bind_uniform_block(data=uniform_data)

        uniform_data = self.uniform_light_data
        uniform_data['LIGHT_POSITION'][...] = main_light.transform.get_pos()
        uniform_data['LIGHT_DIRECTION'][...] = main_light.transform.front
        uniform_data['LIGHT_COLOR'][...] = main_light.light_color
        uniform_data['SHADOW_MATRIX'][...] = main_light.shadow_view_projection
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
            self.renderScene()

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

        # restore
        RenderOption.RENDER_LIGHT_PROBE = False
        RenderOption.RENDER_SKELETON_ACTOR = old_render_skeleton
        RenderOption.RENDER_EFFECT = old_render_effect
        RenderOption.RENDER_FONT = old_render_font
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

    def render_pre_pass(self):
        self.framebuffer_manager.bind_framebuffer(RenderTargets.WORLD_NORMAL, depth_texture=RenderTargets.DEPTHSTENCIL)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        camera = self.scene_manager.main_camera
        self.uniform_view_projection_data['VIEW_PROJECTION'] = camera.view_projection
        self.uniform_view_projection_data['PREV_VIEW_PROJECTION'] = camera.prev_view_projection
        self.uniform_view_projection_buffer.bind_uniform_block(data=self.uniform_view_projection_data)

        # render background normal, depth
        self.render_actors(RenderGroup.STATIC_ACTOR,
                           RenderMode.PRE_PASS,
                           self.scene_manager.static_solid_render_infos,
                           self.pre_pass_material)

        # render velocity
        self.framebuffer_manager.bind_framebuffer(RenderTargets.VELOCITY)
        glClear(GL_COLOR_BUFFER_BIT)

        self.postprocess.render_velocity(RenderTargets.DEPTHSTENCIL)

        # render character normal, velocity
        if RenderOption.RENDER_SKELETON_ACTOR:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.WORLD_NORMAL, RenderTargets.VELOCITY)
            self.render_actors(RenderGroup.SKELETON_ACTOR,
                               RenderMode.PRE_PASS,
                               self.scene_manager.skeleton_solid_render_infos,
                               self.pre_pass_skeletal_material)

    def render_deferred(self):
        self.framebuffer_manager.bind_framebuffer(RenderTargets.DIFFUSE,
                                                  RenderTargets.MATERIAL,
                                                  RenderTargets.WORLD_NORMAL,
                                                  depth_texture=RenderTargets.DEPTHSTENCIL)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        camera = self.scene_manager.main_camera
        self.uniform_view_projection_data['VIEW_PROJECTION'] = camera.view_projection
        self.uniform_view_projection_data['PREV_VIEW_PROJECTION'] = camera.prev_view_projection
        self.uniform_view_projection_buffer.bind_uniform_block(data=self.uniform_view_projection_data)

        # render static gbuffer
        self.render_actors(RenderGroup.STATIC_ACTOR,
                           RenderMode.GBUFFER,
                           self.scene_manager.static_solid_render_infos)

        # render velocity
        self.framebuffer_manager.bind_framebuffer(RenderTargets.VELOCITY)
        glClear(GL_COLOR_BUFFER_BIT)

        self.postprocess.render_velocity(RenderTargets.DEPTHSTENCIL)

        # render character gbuffer
        if RenderOption.RENDER_SKELETON_ACTOR:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.DIFFUSE,
                                                      RenderTargets.MATERIAL,
                                                      RenderTargets.WORLD_NORMAL,
                                                      RenderTargets.VELOCITY,
                                                      depth_texture=RenderTargets.DEPTHSTENCIL)
            self.render_actors(RenderGroup.SKELETON_ACTOR,
                               RenderMode.GBUFFER,
                               self.scene_manager.skeleton_solid_render_infos)

    def render_shadow(self):
        light = self.scene_manager.main_light
        self.uniform_view_projection_data['VIEW_PROJECTION'] = light.shadow_view_projection
        self.uniform_view_projection_data['PREV_VIEW_PROJECTION'] = light.shadow_view_projection
        self.uniform_view_projection_buffer.bind_uniform_block(data=self.uniform_view_projection_data)

        self.render_actors(RenderGroup.STATIC_ACTOR,
                           RenderMode.SHADOW,
                           self.scene_manager.static_shadow_render_infos,
                           self.shadowmap_material)

        if RenderOption.RENDER_SKELETON_ACTOR:
            self.render_actors(RenderGroup.SKELETON_ACTOR,
                               RenderMode.SHADOW,
                               self.scene_manager.skeleton_shadow_render_infos,
                               self.shadowmap_skeletal_material)

    def render_preprocess(self):
        # Linear depth
        self.framebuffer_manager.bind_framebuffer(RenderTargets.LINEAR_DEPTH)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.postprocess.render_linear_depth(RenderTargets.DEPTHSTENCIL, RenderTargets.LINEAR_DEPTH)

        # Screen Space Reflection
        if self.postprocess.is_render_ssr:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.SCREEN_SPACE_REFLECTION)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_screen_space_reflection(RenderTargets.HDR,
                                                            RenderTargets.WORLD_NORMAL,
                                                            RenderTargets.MATERIAL,
                                                            RenderTargets.VELOCITY,
                                                            RenderTargets.LINEAR_DEPTH)

        # SSAO
        if self.postprocess.is_render_ssao:
            temp_ssao = self.rendertarget_manager.get_temporary('temp_ssao', RenderTargets.SSAO)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.SSAO)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_ssao(texture_size=(RenderTargets.SSAO.width, RenderTargets.SSAO.height),
                                         texture_lod=self.rendertarget_manager.texture_lod_in_ssao,
                                         texture_normal=RenderTargets.WORLD_NORMAL,
                                         texture_linear_depth=RenderTargets.LINEAR_DEPTH)
            self.postprocess.render_gaussian_blur(RenderTargets.SSAO, temp_ssao)

    def render_solid(self):
        camera = self.scene_manager.main_camera
        self.uniform_view_projection_data['VIEW_PROJECTION'] = camera.view_projection
        self.uniform_view_projection_data['PREV_VIEW_PROJECTION'] = camera.prev_view_projection
        self.uniform_view_projection_buffer.bind_uniform_block(data=self.uniform_view_projection_data)

        # render solid
        if RenderingType.DEFERRED_RENDERING == self.render_option_manager.rendering_type:
            # render deferred
            self.postprocess.render_deferred_shading(self.scene_manager.get_light_probe_texture(),
                                                     self.scene_manager.atmosphere)
        elif RenderingType.FORWARD_RENDERING == self.render_option_manager.rendering_type:
            # render forward
            self.render_actors(RenderGroup.STATIC_ACTOR,
                               RenderMode.SHADING,
                               self.scene_manager.static_solid_render_infos)
            self.render_actors(RenderGroup.SKELETON_ACTOR,
                               RenderMode.SHADING,
                               self.scene_manager.skeleton_solid_render_infos)

    def render_translucent(self):
        self.render_actors(RenderGroup.STATIC_ACTOR,
                           RenderMode.SHADING,
                           self.scene_manager.static_translucent_render_infos)
        self.render_actors(RenderGroup.SKELETON_ACTOR,
                           RenderMode.SHADING,
                           self.scene_manager.skeleton_translucent_render_infos)

    def render_effect(self):
        self.scene_manager.effect_manager.render()

    def render_actors(self, render_group, render_mode, render_infos, scene_material_instance=None):
        if len(render_infos) < 1:
            return

        last_actor = None
        last_material = None
        last_material_instance = None

        # render
        for render_info in render_infos:
            actor = render_info.actor
            geometry = render_info.geometry
            if scene_material_instance is None:
                material = render_info.material
                material_instance = render_info.material_instance
            else:
                material = scene_material_instance.material
                material_instance = scene_material_instance
            instance_count = actor.instance_count
            is_instancing = 1 < instance_count

            if last_material != material and material is not None:
                material.use_program()

            if last_material_instance != material_instance and material_instance is not None:
                material_instance.bind_material_instance()

            if RenderMode.SHADING == render_mode or RenderMode.GBUFFER == render_mode:
                material_instance.bind_uniform_data('is_render_gbuffer', RenderMode.GBUFFER == render_mode)
                # Render Forward
                if RenderMode.SHADING == render_mode:
                    material_instance.bind_uniform_data('texture_probe', self.scene_manager.get_light_probe_texture())
                    material_instance.bind_uniform_data('texture_shadow', RenderTargets.SHADOWMAP)
                    material_instance.bind_uniform_data('texture_ssao', RenderTargets.SSAO)
                    material_instance.bind_uniform_data('texture_scene_reflect', RenderTargets.SCREEN_SPACE_REFLECTION)
                    # Bind Atmosphere
                    self.scene_manager.atmosphere.bind_precomputed_atmosphere(material_instance)
            elif RenderMode.PRE_PASS == render_mode or RenderMode.SHADOW == render_mode:
                if last_material_instance != material_instance and material_instance:
                    data_diffuse = material_instance.get_uniform_data('texture_diffuse')
                    material_instance.bind_uniform_data('texture_diffuse', data_diffuse)
                    if RenderMode.PRE_PASS == render_mode:
                        data_normal = material_instance.get_uniform_data('texture_normal')
                        material_instance.bind_uniform_data('texture_normal', data_normal)
            elif RenderMode.SELECTED_OBJECT == render_mode:
                pass
            else:
                logger.error("Undefined render mode.")

            if last_actor != actor and material_instance is not None:
                material_instance.bind_uniform_data('is_instancing', is_instancing)
                material_instance.bind_uniform_data('model', actor.transform.matrix)
                if render_group == RenderGroup.SKELETON_ACTOR:
                    animation_buffer = actor.get_animation_buffer(geometry.skeleton.index)
                    prev_animation_buffer = actor.get_prev_animation_buffer(geometry.skeleton.index)
                    material_instance.bind_uniform_data('bone_matrices',
                                                        animation_buffer,
                                                        num=len(animation_buffer))
                    material_instance.bind_uniform_data('prev_bone_matrices',
                                                        prev_animation_buffer,
                                                        num=len(prev_animation_buffer))
            # draw
            if is_instancing:
                self.actor_instance_buffer.bind_instance_buffer(datas=[actor.instance_matrix, ])
                geometry.draw_elements_instanced(instance_count)
            else:
                geometry.draw_elements()

            last_actor = actor
            last_material = material
            last_material_instance = material_instance

    def render_selected_object(self):
        self.set_blend_state(False)
        self.framebuffer_manager.bind_framebuffer(RenderTargets.TEMP_RGBA8)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT)

        # render mask
        selected_object = self.scene_manager.get_selected_object()
        if selected_object is not None:
            object_type = type(selected_object)
            if SkeletonActor == object_type:
                self.render_actors(RenderGroup.SKELETON_ACTOR,
                                   RenderMode.SELECTED_OBJECT,
                                   self.scene_manager.selected_object_render_info,
                                   self.selcted_skeletal_object_material)
            elif StaticActor == object_type:
                self.render_actors(RenderGroup.STATIC_ACTOR,
                                   RenderMode.SELECTED_OBJECT,
                                   self.scene_manager.selected_object_render_info,
                                   self.selcted_static_object_material)
            else:
                return

            # composite
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
            self.selcted_object_composite_material.use_program()
            self.selcted_object_composite_material.bind_uniform_data("texture_mask", RenderTargets.TEMP_RGBA8)
            self.postprocess.draw_elements()

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
                    frame = math.fmod(self.core_manager.currentTime * 30.0, frame_count) if frame_count > 0.0 else 0.0
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
        self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR_PREV)
        glClear(GL_COLOR_BUFFER_BIT)
        self.framebuffer_manager.copy_framebuffer(src_framebuffer)

        # Temporal AA
        if AntiAliasing.TAA == self.postprocess.anti_aliasing:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_temporal_antialiasing(RenderTargets.HDR_PREV,
                                                          RenderTargets.TAA_RESOLVE,
                                                          RenderTargets.VELOCITY,
                                                          RenderTargets.LINEAR_DEPTH)

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
            self.postprocess.render_light_shaft(RenderTargets.ATMOSPHERE,
                                                RenderTargets.LINEAR_DEPTH,
                                                RenderTargets.SHADOWMAP)

        # Depth Of Field
        if self.postprocess.is_render_depth_of_field:
            self.postprocess.render_depth_of_field()

        self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)

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

    def render_font(self):
        self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        self.font_manager.render_font(self.width, self.height)

    def draw_debug_line_2d(self, pos1, pos2, color=[1.0, 1.0, 1.0], width=1.0):
        debug_line = DebugLine(pos1, pos2, color, width)
        self.debug_lines_2d.append(debug_line)

    def draw_debug_line_3d(self, pos1, pos2, color=[1.0, 1.0, 1.0], width=1.0):
        debug_line = DebugLine(pos1, pos2, color, width)
        self.debug_lines_3d.append(debug_line)

    def render_debug_line(self):
        # 2D Line
        glPushMatrix()
        glLoadIdentity()
        for debug_line in self.debug_lines_2d:
            glLineWidth(debug_line.width)
            glColor3f(*debug_line.color)
            glBegin(GL_LINES)
            glVertex3f(*debug_line.pos1, -1.0)
            glVertex3f(*debug_line.pos2, -1.0)
            glEnd()
        self.debug_lines_2d = []
        glPopMatrix()

        # 3D Line
        glPushMatrix()
        glLoadIdentity()
        self.perspective_view(look_at=True)
        for debug_line in self.debug_lines_3d:
            glLineWidth(debug_line.width)
            glColor3f(*debug_line.color)
            glBegin(GL_LINES)
            glVertex3f(*debug_line.pos1)
            glVertex3f(*debug_line.pos2)
            glEnd()
        glPopMatrix()
        self.debug_lines_3d = []

    def renderScene(self):
        startTime = timeModule.perf_counter()

        def end_render_scene():
            glUseProgram(0)
            glFlush()

            endTime = timeModule.perf_counter()
            renderTime = endTime - startTime
            presentTime = 0.0
            return renderTime, presentTime

        main_camera = self.scene_manager.main_camera

        # bind scene constants uniform blocks
        self.bind_uniform_blocks()

        self.set_blend_state(False)
        glPolygonMode(GL_FRONT_AND_BACK, self.viewMode)
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
            # render shader
            self.postprocess.render_material_instance()
        elif RenderOption.RENDER_ONLY_ATMOSPHERE and RenderOption.RENDER_LIGHT_PROBE:
            """ render light probe """
            self.framebuffer_manager.bind_framebuffer(depth_texture=RenderTargets.SHADOWMAP)
            glClearColor(1.0, 1.0, 1.0, 1.0)
            glClear(GL_DEPTH_BUFFER_BIT)

            self.framebuffer_manager.bind_framebuffer(RenderTargets.WORLD_NORMAL,
                                                      depth_texture=RenderTargets.DEPTHSTENCIL)
            glClearColor(0.0, 1.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            self.framebuffer_manager.bind_framebuffer(RenderTargets.LINEAR_DEPTH)
            glClearColor(1.0, 1.0, 1.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_linear_depth(RenderTargets.DEPTHSTENCIL, RenderTargets.LINEAR_DEPTH)

            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

            # render atmosphere
            if self.scene_manager.atmosphere.is_render_atmosphere:
                self.scene_manager.atmosphere.render_precomputed_atmosphere(RenderTargets.LINEAR_DEPTH,
                                                                            RenderTargets.SHADOWMAP,
                                                                            RenderOption.RENDER_LIGHT_PROBE)
            return end_render_scene()
        else:
            """ render normal scene """
            self.scene_manager.ocean.simulateFFTWaves()

            if self.render_option_manager.rendering_type == RenderingType.DEFERRED_RENDERING:
                self.render_deferred()
            else:
                self.render_pre_pass()

            self.render_preprocess()

            self.framebuffer_manager.bind_framebuffer(depth_texture=RenderTargets.SHADOWMAP)
            glClear(GL_DEPTH_BUFFER_BIT)

            glFrontFace(GL_CW)

            self.render_shadow()

            glFrontFace(GL_CCW)

            glDepthMask(False)  # cause depth prepass and gbuffer

            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR, depth_texture=RenderTargets.DEPTHSTENCIL)
            glClear(GL_COLOR_BUFFER_BIT)

            self.render_solid()

            # copy HDR Target
            src_framebuffer = self.framebuffer_manager.get_framebuffer(RenderTargets.HDR)
            dst_framebuffer = self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR_TEMP)
            glClear(GL_COLOR_BUFFER_BIT)
            dst_framebuffer.copy_framebuffer(src_framebuffer)
            src_framebuffer.run_bind_framebuffer()

            # render ocean
            if self.scene_manager.ocean.is_render_ocean:
                self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR, depth_texture=RenderTargets.DEPTHSTENCIL)
                glDisable(GL_CULL_FACE)
                glEnable(GL_DEPTH_TEST)
                glDepthMask(True)

                self.scene_manager.ocean.render_ocean(atmosphere=self.scene_manager.atmosphere,
                                                      texture_scene=RenderTargets.HDR_TEMP,
                                                      texture_linear_depth=RenderTargets.LINEAR_DEPTH,
                                                      texture_probe=RenderTargets.LIGHT_PROBE_ATMOSPHERE,
                                                      texture_shadow=RenderTargets.SHADOWMAP)

                # re copy Linear depth
                self.framebuffer_manager.bind_framebuffer(RenderTargets.LINEAR_DEPTH)
                self.postprocess.render_linear_depth(RenderTargets.DEPTHSTENCIL, RenderTargets.LINEAR_DEPTH)

            # render atmosphere
            if self.scene_manager.atmosphere.is_render_atmosphere:
                self.framebuffer_manager.bind_framebuffer(RenderTargets.ATMOSPHERE,
                                                          RenderTargets.ATMOSPHERE_INSCATTER)
                self.scene_manager.atmosphere.render_precomputed_atmosphere(RenderTargets.LINEAR_DEPTH,
                                                                            RenderTargets.SHADOWMAP,
                                                                            RenderOption.RENDER_LIGHT_PROBE)

            glEnable(GL_CULL_FACE)
            glEnable(GL_DEPTH_TEST)
            glDepthMask(False)

            # Composite Atmosphere & Light Shaft
            if self.scene_manager.atmosphere.is_render_atmosphere:
                self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)

                # composite atmosphere
                self.set_blend_state(True, GL_FUNC_ADD, GL_ONE, GL_ONE_MINUS_SRC_ALPHA)

                composite_atmosphere = self.resource_manager.get_material_instance(
                    "precomputed_atmosphere.composite_atmosphere")
                composite_atmosphere.use_program()
                above_the_cloud = self.scene_manager.atmosphere.cloud_altitude < main_camera.transform.get_pos()[1]
                composite_atmosphere.bind_uniform_data("above_the_cloud", above_the_cloud)
                composite_atmosphere.bind_uniform_data("texture_atmosphere", RenderTargets.ATMOSPHERE)
                composite_atmosphere.bind_uniform_data("texture_inscatter", RenderTargets.ATMOSPHERE_INSCATTER)
                composite_atmosphere.bind_uniform_data("texture_linear_depth", RenderTargets.LINEAR_DEPTH)
                self.postprocess.draw_elements()

            # set blend state
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR, depth_texture=RenderTargets.DEPTHSTENCIL)
            glEnable(GL_DEPTH_TEST)

            self.render_translucent()

            # render particle
            if RenderOption.RENDER_EFFECT:
                glDisable(GL_CULL_FACE)
                glEnable(GL_BLEND)

                self.render_effect()

                glDisable(GL_BLEND)
                glEnable(GL_CULL_FACE)

            if RenderOption.RENDER_LIGHT_PROBE:
                return end_render_scene()

            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

            self.set_blend_state(False)

            self.render_postprocess()

        # selected object
        self.render_selected_object()

        # debug render target
        if self.debug_texture is not None:
            self.set_blend_state(False)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_texture(self.debug_texture)

        if RenderOption.RENDER_FONT:
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.render_font()

        # end of render scene
        OpenGLContext.end_render()

        # draw line
        self.render_debug_line()

        # blit frame buffer
        self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        self.framebuffer_manager.blit_framebuffer(self.width, self.height)
        self.framebuffer_manager.unbind_framebuffer()

        endTime = timeModule.perf_counter()
        renderTime = endTime - startTime
        startTime = endTime

        glFlush()

        # swap buffer
        self.core_manager.game_backend.flip()

        presentTime = timeModule.perf_counter() - startTime
        return renderTime, presentTime
