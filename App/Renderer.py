import os, math
import platform as platformModule
import time as timeModule
import random

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from PIL import Image

from Common import logger, log_level, COMMAND
from Utilities import *
from OpenGLContext import FrameBuffer, FrameBufferManager, RenderBuffer, UniformMatrix4, UniformBlock, CreateTexture
from Object.PostProcess import AntiAliasing, PostProcess
from Object.RenderTarget import RenderTargets
from Object.RenderOptions import RenderOption, RenderingType, RenderGroup, RenderMode


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

        # scene constants uniform buffer
        self.uniformSceneConstants = None
        self.uniformViewConstants = None
        self.uniformViewProjection = None
        self.uniformLightConstants = None
        self.uniformPointLightConstants = None

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

        logger.info("GL_MAX_VERTEX_ATTRIBS: %d" % glGetIntegerv(GL_MAX_VERTEX_ATTRIBS))
        logger.info("GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS: %d" % glGetIntegerv(GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS))
        logger.info("GL_MAX_VERTEX_UNIFORM_COMPONENTS: %d" % glGetIntegerv(GL_MAX_VERTEX_UNIFORM_COMPONENTS))
        logger.info("GL_MAX_VERTEX_UNIFORM_BLOCKS : %d" % glGetIntegerv(GL_MAX_VERTEX_UNIFORM_BLOCKS))
        logger.info("GL_MAX_GEOMETRY_UNIFORM_BLOCKS : %d" % glGetIntegerv(GL_MAX_GEOMETRY_UNIFORM_BLOCKS))
        logger.info("GL_MAX_FRAGMENT_UNIFORM_BLOCKS : %d" % glGetIntegerv(GL_MAX_FRAGMENT_UNIFORM_BLOCKS))
        logger.info("GL_MAX_FRAGMENT_UNIFORM_COMPONENTS: %d" % glGetIntegerv(GL_MAX_FRAGMENT_UNIFORM_COMPONENTS))
        logger.info("GL_MAX_UNIFORM_BLOCK_SIZE : %d" % glGetIntegerv(GL_MAX_UNIFORM_BLOCK_SIZE))
        logger.info("GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT : %d" % glGetIntegerv(GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT))
        logger.info("GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS: %d" % glGetIntegerv(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS))
        logger.info("GL_MAX_DRAW_BUFFERS: %d" % glGetIntegerv(GL_MAX_DRAW_BUFFERS))
        logger.info("GL_MAX_TEXTURE_COORDS: %d" % glGetIntegerv(GL_MAX_TEXTURE_COORDS))
        logger.info("GL_MAX_TEXTURE_IMAGE_UNITS: %d" % glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS))
        logger.info("GL_MAX_VARYING_FLOATS: %d" % glGetIntegerv(GL_MAX_VARYING_FLOATS))

        logger.info("=" * 30)

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

        self.uniformPointLightConstants = UniformBlock("pointLightConstants", program, 4,
                                                       [self.scene_manager.point_light_uniform_blocks, ])

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
            self.framebuffer_manager.clear_framebuffer()
            self.rendertarget_manager.create_rendertargets()
            self.scene_manager.reset_light_probe()
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
        if self.debug_texture is not None:
            self.postprocess.is_render_material_instance = False
            logger.info("Current texture : %s" % self.debug_texture.name)

    def bind_uniform_blocks(self):
        camera = self.scene_manager.main_camera
        main_light = self.scene_manager.main_light

        if not camera or not main_light:
            return

        self.uniformSceneConstants.bind_uniform_block(
            Float4(self.core_manager.currentTime,
                   self.core_manager.frame_count if self.postprocess.anti_aliasing else 0.0,
                   self.postprocess.is_render_ssr,
                   self.postprocess.is_render_ssao),
            Float2(RenderTargets.BACKBUFFER.width, RenderTargets.BACKBUFFER.height),
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
        self.uniformLightConstants.bind_uniform_block(
            main_light.transform.getPos(), FLOAT_ZERO,
            main_light.transform.front, FLOAT_ZERO,
            main_light.light_color,
            main_light.shadow_view_projection
        )

        self.uniformPointLightConstants.bind_uniform_block(self.scene_manager.point_light_uniform_blocks, )

    def renderScene(self):
        startTime = timeModule.perf_counter()

        def end_render_scene():
            glUseProgram(0)
            glFlush()

            endTime = timeModule.perf_counter()
            renderTime = endTime - startTime
            presentTime = 0.0
            return renderTime, presentTime

        # bind scene constants uniform blocks
        self.bind_uniform_blocks()

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

        if self.postprocess.is_render_shader() and not RenderOption.RENDER_LIGHT_PROBE:
            """ debug shader """
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_CULL_FACE)
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
            self.postprocess.bind_quad()
            self.postprocess.render_linear_depth(RenderTargets.DEPTHSTENCIL, RenderTargets.LINEAR_DEPTH)

            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            glDisable(GL_DEPTH_TEST)

            # render atmosphere
            if self.scene_manager.atmosphere.is_render_atmosphere:
                self.scene_manager.atmosphere.render_precomputed_atmosphere(RenderTargets.LINEAR_DEPTH,
                                                                            RenderTargets.SHADOWMAP,
                                                                            not RenderOption.RENDER_LIGHT_PROBE)
            return end_render_scene()
        else:
            """ render normal scene """
            self.scene_manager.ocean.simulateFFTWaves()

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
            self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR, depth_texture=RenderTargets.DEPTHSTENCIL)
            glClear(GL_COLOR_BUFFER_BIT)

            # render solid
            self.render_solid()

            # render atmosphere
            if self.scene_manager.atmosphere.is_render_atmosphere:
                glDisable(GL_DEPTH_TEST)
                prev_framebuffer = self.framebuffer_manager.current_framebuffer
                self.framebuffer_manager.bind_framebuffer(RenderTargets.ATMOSPHERE)
                self.scene_manager.atmosphere.render_precomputed_atmosphere(RenderTargets.LINEAR_DEPTH,
                                                                            RenderTargets.SHADOWMAP,
                                                                            not RenderOption.RENDER_LIGHT_PROBE)

                # set blend state
                self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

                prev_framebuffer.run_bind_framebuffer()
                self.postprocess.bind_quad()
                composite_atmosphere = self.resource_manager.getMaterialInstance(
                    "precomputed_atmosphere.composite_atmosphere")
                composite_atmosphere.use_program()
                composite_atmosphere.bind_uniform_data("texture_atmosphere", RenderTargets.ATMOSPHERE)
                composite_atmosphere.bind_uniform_data("texture_depth", RenderTargets.DEPTHSTENCIL)
                self.postprocess.draw_elements()

            # copy HDR Target
            src_framebuffer = self.framebuffer_manager.get_framebuffer(RenderTargets.HDR)
            dst_framebuffer = self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR_COPY_SMALL)
            glClear(GL_COLOR_BUFFER_BIT)
            dst_framebuffer.copy_framebuffer(src_framebuffer)
            src_framebuffer.run_bind_framebuffer()

            # set blend state
            if not self.blend_enable:
                self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # render ocean
            if self.scene_manager.ocean.is_render_ocean:
                glEnable(GL_DEPTH_TEST)
                glDisable(GL_CULL_FACE)

                self.scene_manager.ocean.render_ocean(atmosphere=self.scene_manager.atmosphere,
                                                      texture_linear_depth=RenderTargets.LINEAR_DEPTH,
                                                      texture_probe=RenderTargets.LIGHT_PROBE_ATMOSPHERE,
                                                      texture_shadow=RenderTargets.SHADOWMAP)
                glEnable(GL_CULL_FACE)

            # render translucent
            glEnable(GL_DEPTH_TEST)
            self.render_translucent()

            if RenderOption.RENDER_LIGHT_PROBE:
                return end_render_scene()

            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_CULL_FACE)
            self.set_blend_state(False)
            self.render_postprocess()

        # debug render target
        if self.debug_texture is not None and self.debug_texture is not RenderTargets.BACKBUFFER and \
                type(self.debug_texture) != RenderBuffer:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_texture(self.debug_texture)

        if RenderOption.RENDER_FONT:
            self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.render_font()

        # reset shader program
        glUseProgram(0)

        # blit frame buffer
        self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        self.framebuffer_manager.blit_framebuffer(self.width, self.height)
        self.framebuffer_manager.unbind_framebuffer()

        # flush
        glFlush()

        endTime = timeModule.perf_counter()
        renderTime = endTime - startTime
        startTime = endTime

        # swap buffer
        self.core_manager.game_backend.flip()

        presentTime = timeModule.perf_counter() - startTime
        return renderTime, presentTime

    def render_light_probe(self, light_probe):
        if light_probe.isRendered:
            return

        logger.info("Rendering Light Probe")

        # Set Valid
        light_probe.isRendered = True

        camera = self.scene_manager.main_camera
        old_pos = camera.transform.getPos().copy()
        old_rot = camera.transform.getRot().copy()
        old_fov = camera.fov
        old_aspect = camera.aspect
        old_render_font = RenderOption.RENDER_FONT
        old_render_skeleton = RenderOption.RENDER_SKELETON_ACTOR

        old_render_motion_blur = self.postprocess.is_render_motion_blur
        old_antialiasing = self.postprocess.anti_aliasing
        old_debug_absolute = self.postprocess.debug_absolute
        old_debug_mipmap = self.postprocess.debug_mipmap
        old_debug_intensity_min = self.postprocess.debug_intensity_min
        old_debug_intensity_max = self.postprocess.debug_intensity_max

        # set render light probe
        RenderOption.RENDER_SKELETON_ACTOR = False
        RenderOption.RENDER_LIGHT_PROBE = True
        RenderOption.RENDER_FONT = False
        self.postprocess.is_render_motion_blur = False
        self.postprocess.anti_aliasing = AntiAliasing.NONE_AA

        camera.update_projection(fov=90.0, aspect=1.0)

        def render_cube_face(dst_texture, target_face, pos, rotation):
            camera.transform.setPos(pos)
            camera.transform.setRot(rotation)
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

        pos = light_probe.transform.getPos()

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

        self.postprocess.bind_quad()

        convolve_environment = self.resource_manager.getMaterialInstance('convolve_environment')
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
        RenderOption.RENDER_FONT = old_render_font
        self.postprocess.is_render_motion_blur = old_render_motion_blur
        self.postprocess.anti_aliasing = old_antialiasing
        self.postprocess.debug_absolute = old_debug_absolute
        self.postprocess.debug_mipmap = old_debug_mipmap
        self.postprocess.debug_intensity_min = old_debug_intensity_min
        self.postprocess.debug_intensity_max = old_debug_intensity_max

        camera.update_projection(old_fov, old_aspect)

        camera.transform.setPos(old_pos)
        camera.transform.setRot(old_rot)
        camera.update(force_update=True)

    def render_pre_pass(self):
        self.framebuffer_manager.bind_framebuffer(RenderTargets.WORLD_NORMAL, depth_texture=RenderTargets.DEPTHSTENCIL)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        camera = self.scene_manager.main_camera
        self.uniformViewProjection.bind_uniform_block(camera.view_projection, camera.prev_view_projection, )

        # render background normal, depth
        self.render_actors(RenderGroup.STATIC_ACTOR,
                           RenderMode.PRE_PASS,
                           self.scene_manager.static_solid_render_infos,
                           self.pre_pass_material)

        # render velocity
        self.postprocess.bind_quad()
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
        self.uniformViewProjection.bind_uniform_block(camera.view_projection, camera.prev_view_projection, )

        # render static gbuffer
        self.render_actors(RenderGroup.STATIC_ACTOR,
                           RenderMode.GBUFFER,
                           self.scene_manager.static_solid_render_infos)

        # render velocity
        self.postprocess.bind_quad()
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
        self.framebuffer_manager.bind_framebuffer(depth_texture=RenderTargets.SHADOWMAP)
        glClear(GL_DEPTH_BUFFER_BIT)

        light = self.scene_manager.main_light
        self.uniformViewProjection.bind_uniform_block(light.shadow_view_projection, light.shadow_view_projection)

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
        self.postprocess.bind_quad()

        # Linear depth
        self.framebuffer_manager.bind_framebuffer(RenderTargets.LINEAR_DEPTH)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.postprocess.render_linear_depth(RenderTargets.DEPTHSTENCIL, RenderTargets.LINEAR_DEPTH)

        # Screen Space Reflection
        if self.postprocess.is_render_ssr:
            self.framebuffer_manager.bind_framebuffer(RenderTargets.SCREEN_SPACE_REFLECTION)
            glClear(GL_COLOR_BUFFER_BIT)
            self.postprocess.render_screen_space_reflection(RenderTargets.HDR, RenderTargets.WORLD_NORMAL,
                                                            RenderTargets.VELOCITY, RenderTargets.DEPTHSTENCIL)

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
        self.uniformViewProjection.bind_uniform_block(camera.view_projection, camera.prev_view_projection)

        # render solid
        if RenderingType.DEFERRED_RENDERING == self.render_option_manager.rendering_type:
            glDisable(GL_DEPTH_TEST)
            self.postprocess.bind_quad()
            # render deferred
            self.postprocess.render_deferred_shading(self.scene_manager.get_light_probe_texture(),
                                                     self.scene_manager.atmosphere)
        elif RenderingType.FORWARD_RENDERING == self.render_option_manager.rendering_type:
            glEnable(GL_DEPTH_TEST)
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

    def render_actors(self, render_group, render_mode, render_infos, scene_material_instance=None):
        if len(render_infos) < 1:
            return

        if scene_material_instance and scene_material_instance.material:
            scene_material_instance.material.use_program()

        last_actor = None
        last_geometry = None
        last_material = None
        last_material_instance = None

        # render
        for render_info in render_infos:
            actor = render_info.actor
            geometry = render_info.geometry
            material = render_info.material
            material_instance = render_info.material_instance

            if RenderMode.SHADING == render_mode or RenderMode.GBUFFER == render_mode:
                if last_material != material:
                    material.use_program()

                if last_material_instance != material_instance and material_instance:
                    scene_material_instance = material_instance
                    material_instance.bind_material_instance()
                    material_instance.bind_uniform_data('is_render_gbuffer', RenderMode.GBUFFER == render_mode)
                    # Render Forward
                    if RenderMode.SHADING == render_mode:
                        material_instance.bind_uniform_data('texture_probe', self.scene_manager.get_light_probe_texture())
                        material_instance.bind_uniform_data('texture_shadow', RenderTargets.SHADOWMAP)
                        material_instance.bind_uniform_data('texture_ssao', RenderTargets.SSAO)
                        material_instance.bind_uniform_data('texture_scene_reflect',
                                                            RenderTargets.SCREEN_SPACE_REFLECTION)
                        # Bind Atmosphere
                        self.scene_manager.atmosphere.bind_precomputed_atmosphere(material_instance)

            elif RenderMode.PRE_PASS == render_mode or RenderMode.SHADOW == render_mode:
                if last_material_instance != material_instance and material_instance:
                    data_diffuse = material_instance.get_uniform_data('texture_diffuse')
                    scene_material_instance.bind_uniform_data('texture_diffuse', data_diffuse)
                    if RenderMode.PRE_PASS == render_mode:
                        data_normal = material_instance.get_uniform_data('texture_normal')
                        scene_material_instance.bind_uniform_data('texture_normal', data_normal)
            else:
                logger.error("Undefined render mode.")

            if last_actor != actor and scene_material_instance:
                scene_material_instance.bind_uniform_data('model', actor.transform.matrix)
                if render_group == RenderGroup.SKELETON_ACTOR:
                    animation_buffer = actor.get_animation_buffer(geometry.skeleton.index)
                    prev_animation_buffer = actor.get_prev_animation_buffer(geometry.skeleton.index)
                    scene_material_instance.bind_uniform_data('bone_matrices',
                                                              animation_buffer,
                                                              len(animation_buffer))
                    scene_material_instance.bind_uniform_data('prev_bone_matrices',
                                                              prev_animation_buffer,
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
        self.framebuffer_manager.bind_framebuffer(RenderTargets.HDR)

        # bind quad mesh
        self.postprocess.bind_quad()

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

        # Tone Map
        self.framebuffer_manager.bind_framebuffer(RenderTargets.BACKBUFFER)
        glClear(GL_COLOR_BUFFER_BIT)
        self.postprocess.render_tone_map(RenderTargets.HDR)

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
