import os, math
import platform as platformModule
import time as timeModule

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from PIL import Image

from Common import logger, log_level, COMMAND
from Utilities import *
from OpenGLContext import FrameBuffer, FrameBufferManager, RenderBuffer, UniformMatrix4, UniformBlock
from .PostProcess import AntiAliasing, PostProcess
from .RenderTarget import RenderTargets
from .RenderOptions import RenderOption, RenderingType, RenderGroup, RenderMode


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
        self.framebuffer = None
        self.framebuffer_shadow = None
        self.framebuffer_copy = None
        self.framebuffer_msaa = None
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
        self.uniformSceneConstants = None
        self.uniformViewConstants = None
        self.uniformViewProjection = None
        self.uniformLightConstants = None

        # material instances
        self.scene_constants_material = None
        self.debug_bone_material = None
        self.pre_pass_material = None
        self.pre_pass_skeletal_material = None
        self.shadowmap_material = None
        self.shadowmap_skeletal_material = None

    def destroyScreen(self):
        self.core_manager.game_backend.quit()

    def initialize(self, core_manager):
        logger.info("=" * 30)
        logger.info("Initialize Renderer")

        logger.info("GL_MAX_VERTEX_UNIFORM_BLOCKS : %d" % glGetIntegerv(GL_MAX_VERTEX_UNIFORM_BLOCKS))
        logger.info("GL_MAX_GEOMETRY_UNIFORM_BLOCKS : %d" % glGetIntegerv(GL_MAX_GEOMETRY_UNIFORM_BLOCKS))
        logger.info("GL_MAX_FRAGMENT_UNIFORM_BLOCKS : %d" % glGetIntegerv(GL_MAX_FRAGMENT_UNIFORM_BLOCKS))
        logger.info("GL_MAX_UNIFORM_BLOCK_SIZE : %d" % glGetIntegerv(GL_MAX_UNIFORM_BLOCK_SIZE))
        logger.info("GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT : %d" % glGetIntegerv(GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT))
        logger.info("=" * 30)

        self.core_manager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.render_option_manager = core_manager.render_option_manager
        self.font_manager = core_manager.font_manager
        self.scene_manager = core_manager.scene_manager
        self.rendertarget_manager = core_manager.rendertarget_manager
        self.postprocess = PostProcess()
        self.postprocess.initialize()

        self.framebuffer_manager = FrameBufferManager()

        self.framebuffer = FrameBuffer()
        self.framebuffer_shadow = FrameBuffer()
        self.framebuffer_copy = FrameBuffer()
        self.framebuffer_msaa = FrameBuffer()

        # material instances
        self.scene_constants_material = self.resource_manager.getMaterialInstance('scene_constants')
        self.debug_bone_material = self.resource_manager.getMaterialInstance("debug_bone")
        self.pre_pass_material = self.resource_manager.getMaterialInstance("pre_pass")
        self.pre_pass_skeletal_material = self.resource_manager.getMaterialInstance(name="pre_pass_skeletal",
                                                                                    shader_name="pre_pass",
                                                                                    macros={"SKELETAL": 1})
        self.shadowmap_material = self.resource_manager.getMaterialInstance("shadowmap")
        self.shadowmap_skeletal_material = self.resource_manager.getMaterialInstance(name="shadowmap_skeletal",
                                                                                     shader_name="shadowmap",
                                                                                     macros={"SKELETAL": 1})

        # scene constants uniform buffer
        program = self.scene_constants_material.get_program()

        self.uniformSceneConstants = UniformBlock("sceneConstants", program, 0,
                                                  [FLOAT4_ZERO,
                                                   FLOAT2_ZERO,
                                                   FLOAT2_ZERO])

        self.uniformViewConstants = UniformBlock("viewConstants", program, 1,
                                                  [MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   FLOAT4_ZERO,
                                                   FLOAT2_ZERO,
                                                   FLOAT2_ZERO,
                                                   FLOAT2_ZERO])

        self.uniformViewProjection = UniformBlock("viewProjection", program, 2,
                                                  [MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY])

        self.uniformLightConstants = UniformBlock("lightConstants", program, 3,
                                                  [FLOAT4_ZERO,
                                                   FLOAT4_ZERO,
                                                   FLOAT4_ZERO,
                                                   MATRIX4_IDENTITY])

        # set gl hint
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

        def get_rendering_type_name(rendering_type):
            rendering_type = str(rendering_type)
            return rendering_type.split('.')[-1] if '.' in rendering_type else rendering_type

        rendering_type_list = [get_rendering_type_name(RenderingType.convert_index_to_enum(x)) for x in
                               range(RenderingType.COUNT.value)]
        # Send to GUI
        self.core_manager.sendRenderingTypeList(rendering_type_list)

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

    def setViewMode(self, viewMode):
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
            self.rendertarget_manager.create_rendertargets()
            self.framebuffer_manager.rebuild_command()
            # cause, rendertargets are cleared.
            if self.scene_manager.atmosphere:
                self.scene_manager.atmosphere.initialize()
        self.core_manager.gc_collect()

    def ortho_view(self):
        # Legacy opengl pipeline - set orthographic view
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def projection_view(self):
        # Legacy opengl pipeline - set perspective view
        camera = self.scene_manager.main_camera
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(camera.fov, self.aspect, camera.near, camera.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_debug_texture(self, texture):
        self.debug_texture = texture
        if self.debug_texture:
            self.postprocess.is_render_material_instance = False
            logger.info("Current texture : %s" % self.debug_texture.name)

    def render_light_probe(self, force=False):
        if not force and self.scene_manager.main_light_probe.isValid:
            return

        logger.info("Rendering Cube map")

        self.scene_manager.main_light_probe.isValid = True

        camera = self.scene_manager.main_camera
        old_pos = camera.transform.getPos().copy()
        old_rot = camera.transform.getRot().copy()
        old_fov = camera.fov
        old_aspect = camera.aspect
        old_render_motion_blur = self.postprocess.is_render_motion_blur
        old_antialiasing = self.postprocess.anti_aliasing
        old_render_font = RenderOption.RENDER_FONT
        old_render_skeleton = RenderOption.RENDER_SKELETON_ACTOR

        # set render light probe
        RenderOption.RENDER_SKELETON_ACTOR = False
        RenderOption.RENDER_LIGHT_PROBE = True
        RenderOption.RENDER_FONT = False
        self.postprocess.is_render_motion_blur = False
        self.postprocess.anti_aliasing = AntiAliasing.NONE_AA

        camera.update_projection(fov=90.0, aspect=1.0)

        def render(pos, pitch, yaw, roll, cube_dir):
            camera.transform.setPos(pos)
            camera.transform.setRot([pitch, yaw, roll])
            camera.update(force_update=True)

            # render
            self.renderScene()

            dst_texture = self.scene_manager.main_light_probe.get_texture(cube_dir)

            self.framebuffer.set_color_textures(RenderTargets.HDR)
            self.framebuffer.bind_framebuffer()
            self.framebuffer_copy.set_color_textures(dst_texture)
            self.framebuffer_copy.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)

            self.framebuffer_copy.mirror_framebuffer(self.framebuffer)

            # generate mipmaps per face
            dst_texture.generate_mipmap()

        self.scene_manager.main_light_probe.generate_texture_faces()
        pos = self.scene_manager.main_light_probe.transform.getPos()
        render(pos, 0.0, math.pi * 0.0, 0.0, "back")
        render(pos, 0.0, math.pi * 0.5, 0.0, "left")
        render(pos, 0.0, math.pi * 1.0, 0.0, "front")
        render(pos, 0.0, math.pi * 1.5, 0.0, "right")
        render(pos, math.pi * -0.5, math.pi * 1.0, 0.0, "top")
        render(pos, math.pi * 0.5, math.pi * 1.0, 0.0, "bottom")

        self.scene_manager.main_light_probe.generate_texture_probe()

        # restore
        RenderOption.RENDER_LIGHT_PROBE = False
        RenderOption.RENDER_SKELETON_ACTOR = old_render_skeleton
        RenderOption.RENDER_FONT = old_render_font
        self.postprocess.is_render_motion_blur = old_render_motion_blur
        self.postprocess.anti_aliasing = old_antialiasing

        camera.update_projection(old_fov, old_aspect)

        camera.transform.setPos(old_pos)
        camera.transform.setRot(old_rot)
        camera.update(force_update=True)

    def renderScene(self):
        startTime = timeModule.perf_counter()

        # bind scene constants
        camera = self.scene_manager.main_camera
        light = self.scene_manager.main_light

        if not camera or not light:
            return

        self.uniformSceneConstants.bind_uniform_block(
            Float4(self.core_manager.currentTime,
                   self.core_manager.frame_count if self.postprocess.anti_aliasing else 0.0,
                   self.postprocess.is_render_ssr,
                   self.postprocess.is_render_ssao),
            Float2(RenderTargets.BACKBUFFER.width,
                   RenderTargets.BACKBUFFER.height),
            self.core_manager.get_mouse_pos(),
        )

        self.uniformViewConstants.bind_uniform_block(camera.view,
                                                     np.linalg.inv(camera.view),
                                                     camera.view_origin,
                                                     np.linalg.inv(camera.view_origin),
                                                     camera.projection,
                                                     np.linalg.inv(camera.projection),
                                                     camera.transform.getPos(), FLOAT_ZERO,
                                                     Float2(camera.near, camera.far),
                                                     self.postprocess.jitter_delta,
                                                     self.postprocess.jitter)

        # light.transform.setPos((math.sin(timeModule.time()) * 20.0, 0.0, math.cos(timeModule.time()) * 20.0))
        self.uniformLightConstants.bind_uniform_block(light.transform.getPos(), FLOAT_ZERO,
                                                      light.transform.front, FLOAT_ZERO,
                                                      light.lightColor,
                                                      light.shadow_view_projection)

        self.set_blend_state(False)
        glPolygonMode(GL_FRONT_AND_BACK, self.viewMode)
        # glEnable(GL_FRAMEBUFFER_SRGB)
        glEnable(GL_MULTISAMPLE)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glFrontFace(GL_CCW)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(True)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        if self.postprocess.enable_render_material_instance() and not RenderOption.RENDER_LIGHT_PROBE:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_CULL_FACE)
            self.set_blend_state(False)
            self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER, depth_texture=None)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_material_instance()
        else:
            # render normal scene
            if self.render_option_manager.rendering_type == RenderingType.DEFERRED_RENDERING:
                self.render_deferred()
            else:
                self.render_pre_pass()

            glDisable(GL_DEPTH_TEST)
            self.render_preprocess()

            glFrontFace(GL_CW)
            glEnable(GL_DEPTH_TEST)
            self.render_shadow()

            glFrontFace(GL_CCW)
            glDepthMask(False)  # cause depth prepass and gbuffer
            self.framebuffer.set_color_textures(RenderTargets.HDR)
            self.framebuffer.set_depth_texture(RenderTargets.DEPTHSTENCIL)
            self.framebuffer.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)

            # render solid
            self.render_solid()

            # atmosphere
            # glDisable(GL_DEPTH_TEST)
            # if self.scene_manager.atmosphere is None:
            #     # simple cubemap atmosphere
            #     self.postprocess.bind_quad()
            #     self.postprocess.render_atmosphere()

            glEnable(GL_DEPTH_TEST)
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # render atmosphere
            if self.scene_manager.atmosphere is not None:
                glDisable(GL_DEPTH_TEST)
                self.scene_manager.atmosphere.render_precomputed_atmosphere(RenderTargets.LINEAR_DEPTH,
                                                                            RenderTargets.WORLD_NORMAL,
                                                                            RenderTargets.SHADOWMAP)

            # render translucent
            glEnable(GL_DEPTH_TEST)
            self.render_translucent()

            if RenderOption.RENDER_LIGHT_PROBE:
                glUseProgram(0)
                endTime = timeModule.perf_counter()
                renderTime = endTime - startTime
                presentTime = 0.0
                return renderTime, presentTime

            glDisable(GL_DEPTH_TEST)
            glDisable(GL_CULL_FACE)
            self.set_blend_state(False)
            self.render_postprocess()

        if RenderOption.RENDER_FONT:
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.render_font()

        # reset shader program
        glUseProgram(0)

        # blit frame buffer
        self.framebuffer.set_color_textures(RenderTargets.BACKBUFFER)
        self.framebuffer.bind_framebuffer()
        self.framebuffer.blit_framebuffer(self.width, self.height)

        # flush
        glFlush()

        endTime = timeModule.perf_counter()
        renderTime = endTime - startTime
        startTime = endTime

        # swap buffer
        self.core_manager.game_backend.flip()

        presentTime = timeModule.perf_counter() - startTime
        return renderTime, presentTime

    def render_pre_pass(self):
        self.framebuffer.set_color_textures(RenderTargets.WORLD_NORMAL)
        self.framebuffer.set_depth_texture(RenderTargets.DEPTHSTENCIL)
        self.framebuffer.bind_framebuffer()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        camera = self.scene_manager.main_camera
        self.uniformViewProjection.bind_uniform_block(camera.view_projection, camera.prev_view_projection, )

        # render background normal, depth
        self.render_actors(RenderGroup.STATIC_ACTOR, RenderMode.PRE_PASS,
                           self.scene_manager.static_solid_render_infos, self.pre_pass_material)

        # render velocity
        self.postprocess.bind_quad()
        self.framebuffer_manager.bind_framebuffer(RenderTargets.VELOCITY, depth_texture=None)
        glClear(GL_COLOR_BUFFER_BIT)

        self.postprocess.render_velocity(RenderTargets.DEPTHSTENCIL)

        # render character normal, velocity
        if RenderOption.RENDER_SKELETON_ACTOR:
            self.framebuffer.set_color_textures(RenderTargets.WORLD_NORMAL, RenderTargets.VELOCITY)
            self.framebuffer.bind_framebuffer()
            self.render_actors(RenderGroup.SKELETON_ACTOR, RenderMode.PRE_PASS,
                               self.scene_manager.skeleton_solid_render_infos, self.pre_pass_skeletal_material)

    def render_deferred(self):
        framebuffer = self.framebuffer_manager.bind_framebuffer(RenderTargets.DIFFUSE,
                                                                RenderTargets.MATERIAL,
                                                                RenderTargets.WORLD_NORMAL,
                                                                depth_texture=RenderTargets.DEPTHSTENCIL)
        framebuffer.clear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT, (0.0, 0.0, 0.0, 0.0))

        camera = self.scene_manager.main_camera
        self.uniformViewProjection.bind_uniform_block(camera.view_projection, camera.prev_view_projection, )

        # render static gbuffer
        self.render_actors(RenderGroup.STATIC_ACTOR, RenderMode.GBUFFER,
                           self.scene_manager.static_solid_render_infos)

        # render velocity
        self.postprocess.bind_quad()
        self.framebuffer_manager.bind_framebuffer(RenderTargets.VELOCITY, depth_texture=None)
        glClear(GL_COLOR_BUFFER_BIT)

        self.postprocess.render_velocity(RenderTargets.DEPTHSTENCIL)

        # render character gbuffer
        if RenderOption.RENDER_SKELETON_ACTOR:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.DIFFUSE,
                                                      RenderTargets.MATERIAL,
                                                      RenderTargets.WORLD_NORMAL,
                                                      RenderTargets.VELOCITY,
                                                      depth_texture=RenderTargets.DEPTHSTENCIL)
            self.render_actors(RenderGroup.SKELETON_ACTOR, RenderMode.GBUFFER,
                               self.scene_manager.skeleton_solid_render_infos)

    def render_shadow(self):
        self.framebuffer_shadow.set_color_textures()
        self.framebuffer_shadow.set_depth_texture(RenderTargets.SHADOWMAP)
        self.framebuffer_shadow.bind_framebuffer()
        glClear(GL_DEPTH_BUFFER_BIT)

        light = self.scene_manager.main_light
        self.uniformViewProjection.bind_uniform_block(light.shadow_view_projection, light.shadow_view_projection)

        self.render_actors(RenderGroup.STATIC_ACTOR, RenderMode.SHADOW,
                           self.scene_manager.static_solid_render_infos, self.shadowmap_material)

        if RenderOption.RENDER_SKELETON_ACTOR:
            self.render_actors(RenderGroup.SKELETON_ACTOR, RenderMode.SHADOW,
                               self.scene_manager.skeleton_solid_render_infos, self.shadowmap_skeletal_material)
            self.framebuffer_shadow.unbind_framebuffer()

    def render_preprocess(self):
        self.postprocess.bind_quad()
        self.framebuffer.set_depth_texture(None)

        # Screen Space Reflection
        if self.postprocess.is_render_ssr:
            self.framebuffer.set_color_textures(RenderTargets.SCREEN_SPACE_REFLECTION)
            self.framebuffer.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)

            self.postprocess.render_screen_space_reflection(RenderTargets.HDR, RenderTargets.WORLD_NORMAL,
                                                            RenderTargets.VELOCITY, RenderTargets.DEPTHSTENCIL)

        # Linear depth
        self.framebuffer.set_color_textures(RenderTargets.LINEAR_DEPTH)
        self.framebuffer.bind_framebuffer()
        glClear(GL_COLOR_BUFFER_BIT)

        self.postprocess.render_linear_depth(RenderTargets.DEPTHSTENCIL)

        # SSAO
        if self.postprocess.is_render_ssao:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.SSAO, depth_texture=None)
            glClear(GL_COLOR_BUFFER_BIT)

            self.postprocess.render_ssao((RenderTargets.SSAO.width, RenderTargets.SSAO.height),
                                         texture_normal=RenderTargets.WORLD_NORMAL,
                                         texture_linear_depth=RenderTargets.LINEAR_DEPTH)

    def render_solid(self):
        camera = self.scene_manager.main_camera
        self.uniformViewProjection.bind_uniform_block(camera.view_projection, camera.prev_view_projection)

        # render solid
        if self.render_option_manager.rendering_type == RenderingType.DEFERRED_RENDERING:
            glDisable(GL_DEPTH_TEST)
            if RenderOption.RENDER_LIGHT_PROBE:
                texture_probe = self.resource_manager.getTexture('field')
            else:
                texture_probe = self.scene_manager.main_light_probe.texture_probe
            self.postprocess.bind_quad()
            # render deferred
            self.postprocess.render_deferred_shading(texture_probe, self.scene_manager.atmosphere)
        elif self.render_option_manager.rendering_type == RenderingType.FORWARD_RENDERING:
            glEnable(GL_DEPTH_TEST)
            self.render_actors(
                RenderGroup.STATIC_ACTOR, RenderMode.LIGHTING, self.scene_manager.static_solid_render_infos)
            self.render_actors(
                RenderGroup.SKELETON_ACTOR, RenderMode.LIGHTING, self.scene_manager.skeleton_solid_render_infos)

    def render_translucent(self):
        self.render_actors(RenderGroup.STATIC_ACTOR, RenderMode.LIGHTING,
                           self.scene_manager.static_translucent_render_infos)
        self.render_actors(RenderGroup.SKELETON_ACTOR, RenderMode.LIGHTING,
                           self.scene_manager.skeleton_translucent_render_infos)

    def render_actors(self, render_group, render_mode, render_infos, material_instance=None):
        if len(render_infos) < 1:
            return

        if material_instance and material_instance.material:
            material_instance.material.use_program()

        if RenderOption.RENDER_LIGHT_PROBE:
            texture_probe = self.resource_manager.getTexture('field')
        else:
            texture_probe = self.scene_manager.main_light_probe.texture_probe

        material = None
        last_actor = None
        last_geometry = None
        last_material = None
        last_material_instance = None

        # render
        for render_info in render_infos:
            actor = render_info.actor
            geometry = render_info.geometry

            if RenderMode.LIGHTING == render_mode or RenderMode.GBUFFER == render_mode:
                material = render_info.material
                material_instance = render_info.material_instance

                if last_material != material:
                    material.use_program()

                if last_material_instance != material_instance:
                    material_instance.bind_material_instance()
                    material_instance.bind_uniform_data('is_render_gbuffer', RenderMode.GBUFFER == render_mode)
                    if RenderMode.LIGHTING == render_mode:
                        material_instance.bind_uniform_data('texture_probe', texture_probe)
                        material_instance.bind_uniform_data('texture_shadow', RenderTargets.SHADOWMAP)
                        material_instance.bind_uniform_data('texture_ssao', RenderTargets.SSAO)
                        material_instance.bind_uniform_data('texture_scene_reflect',
                                                            RenderTargets.SCREEN_SPACE_REFLECTION)
            elif RenderMode.PRE_PASS == render_mode or RenderMode.SHADOW == render_mode:
                if last_material_instance != material_instance and material_instance:
                    data_diffuse = material_instance.get_uniform_data('texture_diffuse')
                    material_instance.bind_uniform_data('texture_diffuse', data_diffuse)
                    if RenderMode.PRE_PASS == render_mode:
                        data_normal = material_instance.get_uniform_data('texture_normal')
                        material_instance.bind_uniform_data('texture_normal', data_normal)
            else:
                logger.error("Undefined render mode.")

            if True or last_actor != actor and material_instance:
                material_instance.bind_uniform_data('model', actor.transform.matrix)
                if render_group == RenderGroup.SKELETON_ACTOR:
                    animation_buffer = actor.get_animation_buffer(geometry.skeleton.index)
                    prev_animation_buffer = actor.get_prev_animation_buffer(geometry.skeleton.index)
                    material_instance.bind_uniform_data('bone_matrices', animation_buffer, len(animation_buffer))
                    material_instance.bind_uniform_data('prev_bone_matrices', prev_animation_buffer,
                                                        len(prev_animation_buffer))

            if last_geometry != geometry:
                geometry.bind_vertex_buffer()

            # draw
            geometry.draw_elements()

            last_actor = actor
            last_geometry = geometry
            last_material = material
            last_material_instance = material_instance

    def render_bones(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        mesh = self.resource_manager.getMesh("Cube")
        static_actors = self.scene_manager.static_actors[:]

        if mesh and self.debug_bone_material:
            material_instance = self.debug_bone_material
            material_instance.use_program()
            material_instance.bind()
            mesh.bind_vertex_buffer()

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
        self.framebuffer.set_color_textures(RenderTargets.HDR)
        self.framebuffer.set_depth_texture(None)
        self.framebuffer.bind_framebuffer()

        # Atmosphere demo
        # self.scene_manager.atmosphere.render_precomputed_atmosphere_demo(RenderTargets.LINEAR_DEPTH,
        #                                                                  RenderTargets.WORLD_NORMAL,
        #                                                                  RenderTargets.SHADOWMAP)

        # bind quad mesh
        self.postprocess.bind_quad()

        # Bloom
        if self.postprocess.is_render_bloom:
            self.postprocess.render_bloom(self.framebuffer, RenderTargets.HDR)

        # Blur Test
        # hdr_copy = self.rendertarget_manager.get_temporary('hdr_copy', RenderTargets.HDR)
        # self.postprocess.render_gaussian_blur(self.framebuffer, RenderTargets.HDR, hdr_copy)

        # copy HDR target
        self.framebuffer.set_color_textures(RenderTargets.HDR)
        self.framebuffer.bind_framebuffer()
        self.framebuffer_copy.set_color_textures(RenderTargets.HDR_PREV)
        self.framebuffer_copy.bind_framebuffer()
        glClear(GL_COLOR_BUFFER_BIT)
        self.framebuffer_copy.copy_framebuffer(self.framebuffer)

        # Temporal AA
        if AntiAliasing.TAA == self.postprocess.anti_aliasing:
            self.framebuffer.set_color_textures(RenderTargets.HDR)
            self.framebuffer.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_temporal_antialiasing(RenderTargets.HDR_PREV,
                                                          RenderTargets.TAA_RESOLVE,
                                                          RenderTargets.VELOCITY,
                                                          RenderTargets.LINEAR_DEPTH)

            self.framebuffer.set_color_textures(RenderTargets.HDR)
            self.framebuffer.bind_framebuffer()
            self.framebuffer_copy.set_color_textures(RenderTargets.TAA_RESOLVE)
            self.framebuffer_copy.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)
            self.framebuffer_copy.copy_framebuffer(self.framebuffer)

        # Tone Map
        self.framebuffer.set_color_textures(RenderTargets.BACKBUFFER)
        self.framebuffer.bind_framebuffer()
        glClear(GL_COLOR_BUFFER_BIT)
        self.postprocess.render_tone_map(RenderTargets.HDR)

        # MSAA Test
        if AntiAliasing.MSAA == self.postprocess.anti_aliasing:
            self.framebuffer.set_color_textures(RenderTargets.BACKBUFFER)
            self.framebuffer.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)
            self.framebuffer_msaa.set_color_textures(RenderTargets.HDR)
            self.framebuffer_msaa.bind_framebuffer()
            # resolve MSAA
            self.framebuffer.copy_framebuffer(self.framebuffer_msaa)

        # Motion Blur
        if self.postprocess.is_render_motion_blur:
            backbuffer_copy = self.rendertarget_manager.get_temporary('backbuffer_copy', RenderTargets.BACKBUFFER)
            self.framebuffer.set_color_textures(backbuffer_copy)
            self.framebuffer.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_motion_blur(RenderTargets.VELOCITY, RenderTargets.BACKBUFFER)

            # copy to backbuffer
            self.framebuffer.set_color_textures(backbuffer_copy)
            self.framebuffer.bind_framebuffer()
            self.framebuffer_copy.set_color_textures(RenderTargets.BACKBUFFER)
            self.framebuffer_copy.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)
            self.framebuffer_copy.copy_framebuffer(self.framebuffer)

        # debug render target
        if self.debug_texture and self.debug_texture is not RenderTargets.BACKBUFFER and \
                type(self.debug_texture) != RenderBuffer:
            self.framebuffer.set_color_textures(RenderTargets.BACKBUFFER)
            self.framebuffer.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_texture(self.debug_texture)

    def render_font(self):
        self.framebuffer.set_color_textures(RenderTargets.BACKBUFFER)
        self.framebuffer.bind_framebuffer()
        self.font_manager.render_font(self.width, self.height)
