import os, math
import platform as platformModule
import time as timeModule

import pygame
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from Common import logger, log_level, COMMAND
from Utilities import *
from OpenGLContext import FrameBuffer, RenderBuffer, GLFont, UniformMatrix4, UniformBlock
from .PostProcess import AntiAliasing, PostProcess
from .RenderTarget import RenderTargets


class RenderMode(AutoEnum):
    LIGHTING = ()
    SHADOW = ()
    SCREEN_SPACE_REFLECTION = ()
    VELOCITY = ()
    COUNT = ()


class Console:
    def __init__(self):
        self.infos = []
        self.debugs = []
        self.renderer = None
        self.texture = None
        self.font = None
        self.enable = True

    def initialize(self, renderer):
        self.renderer = renderer
        self.font = GLFont(self.renderer.coreManager.resource_manager.DefaultFontFile, 12, margin=(10, 0))

    def close(self):
        pass

    def clear(self):
        self.infos = []

    def toggle(self):
        self.enable = not self.enable

    # just print info
    def info(self, text):
        if self.enable:
            self.infos.append(text)

    # debug text - print every frame
    def debug(self, text):
        if self.enable:
            self.debugs.append(text)

    def render(self):
        self.renderer.ortho_view()

        # set render state
        self.renderer.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDisable(GL_LIGHTING)

        if self.enable and self.infos:
            text = '\n'.join(self.infos) if len(self.infos) > 1 else self.infos[0]
            if text:
                # render
                self.font.render(text, 0, self.renderer.height - self.font.height)
            self.infos = []


class Renderer(Singleton):
    def __init__(self):
        self.width = 0
        self.height = 0
        self.aspect = 0.0
        self.full_screen = False
        self.viewMode = GL_FILL
        self.created_scene = False
        # managers
        self.coreManager = None
        self.resource_manager = None
        self.sceneManager = None
        self.rendertarget_manager = None
        self.postprocess = None
        # console font
        self.console = None
        # components
        self.lastShader = None
        self.screen = None
        self.framebuffer = None
        self.framebuffer_copy = None
        self.framebuffer_msaa = None
        self.debug_rendertarget = None  # Texture2D

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
        self.sceneConstants_Time = Float4(0.0, 0.0, 0.0, 0.0)
        self.uniformViewConstants = None
        self.uniformViewProjection = None
        self.uniformLightConstants = None

    @staticmethod
    def destroyScreen():
        # destroy
        pygame.display.quit()

    def initialize(self, core_manager, width, height, screen):
        logger.info("=" * 30)
        logger.info("Initialize Renderer")
        self.width = width
        self.height = height
        self.screen = screen

        logger.info("GL_MAX_VERTEX_UNIFORM_BLOCKS : %d" % glGetIntegerv(GL_MAX_VERTEX_UNIFORM_BLOCKS))
        logger.info("GL_MAX_GEOMETRY_UNIFORM_BLOCKS : %d" % glGetIntegerv(GL_MAX_GEOMETRY_UNIFORM_BLOCKS))
        logger.info("GL_MAX_FRAGMENT_UNIFORM_BLOCKS : %d" % glGetIntegerv(GL_MAX_FRAGMENT_UNIFORM_BLOCKS))
        logger.info("GL_MAX_UNIFORM_BLOCK_SIZE : %d" % glGetIntegerv(GL_MAX_UNIFORM_BLOCK_SIZE))
        logger.info("GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT : %d" % glGetIntegerv(GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT))
        logger.info("=" * 30)

        self.coreManager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.sceneManager = core_manager.sceneManager
        self.rendertarget_manager = core_manager.rendertarget_manager
        self.postprocess = PostProcess()
        self.postprocess.initialize()

        self.framebuffer = FrameBuffer()
        self.framebuffer_copy = FrameBuffer()
        self.framebuffer_msaa = FrameBuffer()

        # console font
        self.console = Console()
        self.console.initialize(self)

        # Test Code : scene constants uniform buffer
        material_instance = self.resource_manager.getMaterialInstance('scene_constants')
        program = material_instance.get_program()

        self.uniformSceneConstants = UniformBlock("sceneConstants", program, 0,
                                                  [FLOAT4_ZERO, ])

        self.uniformViewConstants = UniformBlock("viewConstants", program, 1,
                                                  [MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   FLOAT4_ZERO,
                                                   FLOAT4_ZERO])

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

    def close(self):
        # destroy console
        if self.console:
            self.console.close()

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
        self.set_blend_state(self.blend_enable_prev, self.blend_equation_prev, self.blend_func_src_prev,
                             self.blend_func_dst_prev)

    def setViewMode(self, viewMode):
        if viewMode == COMMAND.VIEWMODE_WIREFRAME:
            self.viewMode = GL_LINE
        elif viewMode == COMMAND.VIEWMODE_SHADING:
            self.viewMode = GL_FILL

    @staticmethod
    def change_resolution(width=0, height=0, full_screen=False):
        option = OPENGL | DOUBLEBUF | HWPALETTE | HWSURFACE
        if full_screen:
            option |= FULLSCREEN
        return pygame.display.set_mode((width, height), option)

    def resizeScene(self, width=0, height=0, full_screen=False):
        # You have to do pygame.display.set_mode again on Linux.
        if width <= 0 or height <= 0:
            width = self.width
            height = self.height
            if width <= 0:
                width = 1024
            if height <= 0:
                height = 768

        self.width = width
        self.height = height
        self.aspect = float(width) / float(height)
        self.full_screen = full_screen

        logger.info("resizeScene %d x %d : %s" % (width, height, "Full screen" if full_screen else "Windowed"))

        # update perspective and ortho
        self.sceneManager.update_camera_projection_matrix(self.aspect)

        # resize render targets
        self.rendertarget_manager.create_rendertargets()

        # Run pygame.display.set_mode at last!!! very important.
        if platformModule.system() == 'Linux':
            self.screen = self.change_resolution(width, height, full_screen)
        # send screen info
        screen_info = (width, height, full_screen)
        self.coreManager.notifyChangeResolution(screen_info)
        self.created_scene = True

    def ortho_view(self):
        # Legacy opengl pipeline - set orthographic view
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def projection_view(self):
        # Legacy opengl pipeline - set perspective view
        camera = self.sceneManager.mainCamera
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(camera.fov, self.aspect, camera.near, camera.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_debug_rendertarget(self, rendertarget_index, rendertarget_name):
        self.debug_rendertarget = self.rendertarget_manager.find_rendertarget(rendertarget_index, rendertarget_name)
        logger.info("Current render target : %s" % self.debug_rendertarget.name)

    def renderScene(self):
        startTime = timeModule.perf_counter()

        # bind scene constants
        camera = self.sceneManager.mainCamera
        light = self.sceneManager.mainLight

        if not camera or not light:
            return

        self.sceneConstants_Time[0] = self.coreManager.currentTime
        self.uniformSceneConstants.bind_uniform_block(self.sceneConstants_Time)

        self.uniformViewConstants.bind_uniform_block(camera.view,
                                                     np.linalg.inv(camera.view),
                                                     camera.view_origin,
                                                     np.linalg.inv(camera.view_origin),
                                                     camera.projection,
                                                     np.linalg.inv(camera.projection),
                                                     camera.transform.getPos(), FLOAT_ZERO,
                                                     Float4(camera.near, camera.far, 0.0, 0.0))

        # light.transform.setPos((math.sin(timeModule.time()) * 20.0, 0.0, math.cos(timeModule.time()) * 20.0))
        self.uniformLightConstants.bind_uniform_block(light.transform.getPos(), FLOAT_ZERO,
                                                      light.transform.front, FLOAT_ZERO,
                                                      light.lightColor,
                                                      light.shadow_view_projection)

        # glEnable(GL_FRAMEBUFFER_SRGB)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glFrontFace(GL_CCW)
        glEnable(GL_CULL_FACE)
        self.set_blend_state(False)
        glPolygonMode(GL_FRONT_AND_BACK, self.viewMode)

        self.render_shadow()

        self.render_lighting()

        # self.render_bones()
        self.render_postprocess()

        # reset shader program
        glUseProgram(0)

        # render text
        self.console.render()

        # blit frame buffer
        backbuffer = self.rendertarget_manager.get_rendertarget(RenderTargets.BACKBUFFER)
        self.framebuffer.set_color_texture(backbuffer)
        self.framebuffer.bind_framebuffer()
        self.framebuffer.blit_framebuffer(self.width, self.height)

        endTime = timeModule.perf_counter()
        renderTime = endTime - startTime
        startTime = endTime

        # swap buffer
        pygame.display.flip()
        presentTime = timeModule.perf_counter() - startTime
        return renderTime, presentTime

    def render_shadow(self):
        glFrontFace(GL_CW)
        shadowmap = self.rendertarget_manager.get_rendertarget(RenderTargets.SHADOWMAP)

        self.framebuffer.set_color_texture(None)
        self.framebuffer.set_depth_texture(shadowmap)
        self.framebuffer.bind_framebuffer()
        glClearBufferfv(GL_DEPTH, 0, (1.0, 1.0, 1.0, 1.0))

        light = self.sceneManager.mainLight
        self.uniformViewProjection.bind_uniform_block(light.shadow_view_projection,
                                                      light.shadow_view_projection,)

        self.render_static_actors(render_mode=RenderMode.SHADOW)
        self.render_skeleton_actors(render_mode=RenderMode.SHADOW)

    def render_lighting(self):
        glFrontFace(GL_CCW)

        # render object
        hdrtexture = self.rendertarget_manager.get_rendertarget(RenderTargets.HDR)
        diffusetexture = self.rendertarget_manager.get_rendertarget(RenderTargets.DIFFUSE)
        normaltexture = self.rendertarget_manager.get_rendertarget(RenderTargets.WORLD_NORMAL)
        depthtexture = self.rendertarget_manager.get_rendertarget(RenderTargets.DEPTHSTENCIL)
        velocity_texture = self.rendertarget_manager.get_rendertarget(RenderTargets.VELOCITY)

        self.framebuffer.set_color_texture(hdrtexture)
        self.framebuffer.set_depth_texture(depthtexture)
        self.framebuffer.bind_framebuffer()
        glClearBufferfv(GL_DEPTH, 0, (1.0, 1.0, 1.0, 1.0))

        camera = self.sceneManager.mainCamera
        self.uniformViewProjection.bind_uniform_block(camera.view_projection,
                                                      camera.prev_view_projection, )

        # render sky
        glDisable(GL_DEPTH_TEST)
        self.sceneManager.sky.render()
        glEnable(GL_DEPTH_TEST)

        self.framebuffer.set_color_textures([hdrtexture, diffusetexture, normaltexture, velocity_texture])
        self.framebuffer.bind_framebuffer()
        glClearBufferfv(GL_COLOR, 3, (0.0, 0.0, 0.0, 0.0))

        camera = self.sceneManager.mainCamera
        self.uniformViewProjection.bind_uniform_block(camera.view_projection,
                                                      camera.prev_view_projection, )

        # render character lighting
        self.render_static_actors(render_mode=RenderMode.LIGHTING)
        self.render_skeleton_actors(render_mode=RenderMode.LIGHTING)

    def render_static_actors(self, render_mode: RenderMode):
        if len(self.sceneManager.static_actors) < 1:
            return

        geometries = []
        for static_actor in self.sceneManager.static_actors:
            geometries += static_actor.geometries
        geometries.sort(key=lambda x: id(x.vertex_buffer))

        material = None
        material_instance = None
        default_material_instance = self.resource_manager.getDefaultMaterialInstance()

        last_vertex_buffer = None
        last_actor = None
        last_material = None
        last_material_instance = None

        shadow_texture = self.rendertarget_manager.get_rendertarget(RenderTargets.SHADOWMAP)

        if render_mode == RenderMode.SHADOW:
            material_instance = self.resource_manager.getMaterialInstance("shadowmap")
            material = material_instance.material if material_instance else None

        for geometry in geometries:
            actor = geometry.parent_actor

            if render_mode == RenderMode.LIGHTING:
                material_instance = geometry.get_material_instance() or default_material_instance
                material = material_instance.material if material_instance else None

            if last_material != material and material is not None:
                material.use_program()

            if last_material_instance != material_instance and material_instance is not None:
                material_instance.bind_material_instance()
                if render_mode == RenderMode.LIGHTING:
                    material_instance.bind_uniform_data('shadow_texture', shadow_texture)

            if last_actor != actor and material_instance:
                material_instance.bind_uniform_data('model', actor.transform.matrix)

            # At last, bind buffers
            if geometry is not None and last_vertex_buffer != geometry.vertex_buffer:
                geometry.bind_vertex_buffer()

            # draw
            if geometry and material_instance:
                geometry.draw_elements()

            last_actor = actor
            last_material = material
            last_vertex_buffer = geometry.vertex_buffer
            last_material_instance = material_instance

    def render_skeleton_actors(self, render_mode: RenderMode):
        if len(self.sceneManager.skeleton_actors) < 1:
            return

        camera = self.sceneManager.mainCamera
        camera_pos = camera.transform.getPos()
        camera_front = camera.front

        geometries = []
        for skeleton_actor in self.sceneManager.skeleton_actors:
            geometries += skeleton_actor.geometries
            # actor_dir = normalize(skeleton_actor.transform.getPos() - camera_pos)
            # if np.dot(actor_dir, camera_front) > 0.3:
            #     geometries += skeleton_actor.geometries

        geometries.sort(key=lambda x: id(x.vertex_buffer))

        material = None
        material_instance = None
        default_material_instance = self.resource_manager.getDefaultMaterialInstance()

        last_vertex_buffer = None
        last_actor = None
        last_material = None
        last_material_instance = None

        shadow_texture = self.rendertarget_manager.get_rendertarget(RenderTargets.SHADOWMAP)

        if render_mode == RenderMode.SHADOW:
            material_instance = self.resource_manager.getMaterialInstance("shadowmap_skeleton")
            material = material_instance.material if material_instance else None

        for geometry in geometries:
            actor = geometry.parent_actor

            if render_mode == RenderMode.LIGHTING:
                material_instance = geometry.get_material_instance() or default_material_instance
                material = material_instance.material if material_instance else None

            if last_material != material and material is not None:
                material.use_program()

            if last_material_instance != material_instance and material_instance is not None:
                material_instance.bind_material_instance()
                if render_mode == RenderMode.LIGHTING:
                    material_instance.bind_uniform_data('shadow_texture', shadow_texture)

            if last_actor != actor and material_instance:
                material_instance.bind_uniform_data('model', actor.transform.matrix)
                animation_buffer = actor.get_animation_buffer(geometry.skeleton.index)
                prev_animation_buffer = actor.get_prev_animation_buffer(geometry.skeleton.index)
                material_instance.bind_uniform_data('bone_matrices', animation_buffer, len(animation_buffer))
                material_instance.bind_uniform_data('prev_bone_matrices', prev_animation_buffer,
                                                    len(prev_animation_buffer))

            # At last, bind buffers
            if geometry is not None and last_vertex_buffer != geometry.vertex_buffer:
                geometry.bind_vertex_buffer()

            # draw
            if geometry and material_instance:
                geometry.draw_elements()

            last_actor = actor
            last_material = material
            last_vertex_buffer = geometry.vertex_buffer
            last_material_instance = material_instance

    def render_bones(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        mesh = self.resource_manager.getMesh("Cube")
        material_instance = self.resource_manager.getMaterialInstance("debug_bone")
        static_actors = self.sceneManager.static_actors[:]

        if mesh and material_instance:
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
                    frame = math.fmod(self.coreManager.currentTime * 30.0, frame_count) if frame_count > 0.0 else 0.0
                    isAnimation = frame_count > 0.0
                    for skeleton in skeletons:
                        matrix = static_actor.transform.matrix
                        for bone in skeleton.hierachy:
                            draw_bone(mesh, skeleton_mesh, Matrix4().copy(), material_instance, bone, matrix, isAnimation)

    def render_postprocess(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

        hdrtexture = self.rendertarget_manager.get_rendertarget(RenderTargets.HDR)
        backbuffer = self.rendertarget_manager.get_rendertarget(RenderTargets.BACKBUFFER)
        backbuffer_copy = self.rendertarget_manager.get_temporary('backbuffer_copy', backbuffer)
        texture_diffuse = self.rendertarget_manager.get_rendertarget(RenderTargets.DIFFUSE)
        texture_normal = self.rendertarget_manager.get_rendertarget(RenderTargets.WORLD_NORMAL)
        texture_depth = self.rendertarget_manager.get_rendertarget(RenderTargets.DEPTHSTENCIL)
        texture_linear_depth = self.rendertarget_manager.get_rendertarget(RenderTargets.LINEAR_DEPTH)
        texture_velocity = self.rendertarget_manager.get_rendertarget(RenderTargets.VELOCITY)
        texture_ssao = self.rendertarget_manager.get_rendertarget(RenderTargets.SSAO)
        texture_ssr = self.rendertarget_manager.get_rendertarget(RenderTargets.SCREEN_SPACE_REFLECTION)

        self.set_blend_state(True, GL_FUNC_ADD, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # render fog
        self.framebuffer.set_color_texture(hdrtexture)
        self.framebuffer.set_depth_texture(None)
        self.framebuffer.bind_framebuffer()
        self.sceneManager.fog.render()

        # bind quad mesh
        self.postprocess.bind_quad()

        self.set_blend_state(False)

        # Linear depth
        self.framebuffer.set_color_texture(texture_linear_depth)
        self.framebuffer.bind_framebuffer()
        self.postprocess.render_linear_depth(texture_depth)

        # SSAO
        if self.postprocess.is_render_ssao:
            ssao_temp = self.rendertarget_manager.get_temporary('ssao_temp', texture_ssao)
            self.postprocess.render_ssao(framebuffer=self.framebuffer,
                                         texture_ssao=texture_ssao,
                                         ssao_temp=ssao_temp,
                                         texture_normal=texture_normal,
                                         texture_linear_depth=texture_linear_depth)
        # Bloom
        if self.postprocess.is_render_bloom:
            self.postprocess.render_bloom(self.framebuffer, hdrtexture)

        # self.framebuffer.set_color_texture(texture_ssr)
        # self.framebuffer.set_depth_texture(None)
        # self.framebuffer.bind_framebuffer()
        # self.framebuffer.clear(GL_COLOR_BUFFER_BIT)

        # self.postprocess.render_screen_space_reflection(texture_diffuse, texture_normal, texture_depth)

        # Blur Test
        # hdr_copy = self.rendertarget_manager.get_temporary('hdr_copy', hdrtexture)
        # self.postprocess.render_gaussian_blur(self.framebuffer, hdrtexture, hdr_copy)

        # Tone Map
        self.framebuffer.set_color_texture(backbuffer)
        self.framebuffer.bind_framebuffer()
        self.postprocess.render_tone_map(hdrtexture, texture_ssao)

        # MSAA Test
        if AntiAliasing.MSAA == self.postprocess.antialiasing:
            self.framebuffer.set_color_texture(backbuffer)
            self.framebuffer.bind_framebuffer()
            self.framebuffer_msaa.set_color_texture(hdrtexture)
            self.framebuffer_msaa.bind_framebuffer()
            # resolve
            self.framebuffer.copy_framebuffer(self.framebuffer_msaa)

        # Motion Blur
        self.framebuffer.set_color_texture(backbuffer_copy)
        self.framebuffer.bind_framebuffer()
        self.postprocess.render_motion_blur(texture_velocity, backbuffer)

        # copy to backbuffer
        self.framebuffer.set_color_texture(backbuffer_copy)
        self.framebuffer.bind_framebuffer()
        self.framebuffer_copy.set_color_texture(backbuffer)
        self.framebuffer_copy.bind_framebuffer()
        self.framebuffer_copy.copy_framebuffer(self.framebuffer)

        if self.debug_rendertarget and self.debug_rendertarget is not backbuffer and \
                type(self.debug_rendertarget) != RenderBuffer:
            self.framebuffer.set_color_texture(backbuffer)
            self.framebuffer.bind_framebuffer()
            self.postprocess.render_copy_rendertarget(self.debug_rendertarget)
