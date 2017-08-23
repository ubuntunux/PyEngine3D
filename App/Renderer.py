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
from Object import Camera, Light
from OpenGLContext import RenderTargets, FrameBuffer, GLFont, UniformMatrix4, UniformBlock


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
        glEnable(GL_BLEND)
        glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
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
        self.width = 1024
        self.height = 768
        self.aspect = float(self.width) / float(self.height)
        self.viewMode = GL_FILL
        # managers
        self.coreManager = None
        self.resource_manager = None
        self.sceneManager = None
        self.rendertarget_manager = None
        # console font
        self.console = None
        # components
        self.lastShader = None
        self.screen = None
        self.framebuffer = None
        self.debug_rendertarget = None  # Texture2D

        # postprocess
        self.tonemapping = None
        self.screeen_space_reflection = None
        self.motion_blur = None
        self.copy_rendertarget = None

        # Test Code : scene constants uniform buffer
        self.uniformSceneConstants = None
        self.uniformLightConstants = None

    @staticmethod
    def destroyScreen():
        # destroy
        pygame.display.quit()

    def initialize(self, core_manager, width, height, screen):
        logger.info("Initialize Renderer")
        self.width = width
        self.height = height
        self.screen = screen

        self.coreManager = core_manager
        self.resource_manager = core_manager.resource_manager
        self.sceneManager = core_manager.sceneManager
        self.rendertarget_manager = core_manager.rendertarget_manager

        self.framebuffer = FrameBuffer()

        # console font
        self.console = Console()
        self.console.initialize(self)

        # postprocess
        self.tonemapping = self.resource_manager.getMaterialInstance("tonemapping")
        self.motion_blur = self.resource_manager.getMaterialInstance("motion_blur")
        self.screeen_space_reflection = self.resource_manager.getMaterialInstance("screen_space_reflection")
        self.copy_rendertarget = self.resource_manager.getMaterialInstance("copy_rendertarget")

        # Test Code : scene constants uniform buffer
        material_instance = self.resource_manager.getMaterialInstance('scene_constants')
        program = material_instance.get_program()
        self.uniformSceneConstants = UniformBlock("sceneConstants", program, 0,
                                                  [MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   MATRIX4_IDENTITY,
                                                   FLOAT4_ZERO,
                                                   FLOAT4_ZERO])
        self.uniformLightConstants = UniformBlock("lightConstants", program, 1,
                                                  [FLOAT4_ZERO,
                                                   FLOAT4_ZERO,
                                                   FLOAT4_ZERO])

        # set gl hint
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    def close(self):
        # destroy console
        if self.console:
            self.console.close()

    def setViewMode(self, viewMode):
        if viewMode == COMMAND.VIEWMODE_WIREFRAME:
            self.viewMode = GL_LINE
        elif viewMode == COMMAND.VIEWMODE_SHADING:
            self.viewMode = GL_FILL

    def resizeScene(self, width=0, height=0):
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

        # update perspective and ortho
        camera = self.sceneManager.getMainCamera()
        camera.update_projection(self.aspect)

        # resize render targets
        self.rendertarget_manager.create_rendertargets(self.width, self.height)

        # Run pygame.display.set_mode at last!!! very important.
        if platformModule.system() == 'Linux':
            self.screen = pygame.display.set_mode((self.width, self.height),
                                                  OPENGL | DOUBLEBUF | RESIZABLE | HWPALETTE | HWSURFACE)

    def ortho_view(self):
        # Legacy opengl pipeline - set orthographic view
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def projection_view(self):
        # Legacy opengl pipeline - set perspective view
        camera = self.sceneManager.getMainCamera()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(camera.fov, self.aspect, camera.near, camera.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def renderScene(self):
        startTime = timeModule.perf_counter()

        # bind scene constants
        camera = self.sceneManager.getMainCamera()
        lights = self.sceneManager.get_object_list(Light)

        if not camera or len(lights) < 1:
            return

        self.render_objects_begin()

        # render object
        colortexture = self.rendertarget_manager.get_rendertarget(RenderTargets.BACKBUFFER)
        diffusetexture = self.rendertarget_manager.get_rendertarget(RenderTargets.DIFFUSE)
        normaltexture = self.rendertarget_manager.get_rendertarget(RenderTargets.WORLD_NORMAL)
        depthtexture = self.rendertarget_manager.get_rendertarget(RenderTargets.DEPTHSTENCIL)
        shadowmap = self.rendertarget_manager.get_rendertarget(RenderTargets.SHADOWMAP)
        velocity_texture = self.rendertarget_manager.get_rendertarget(RenderTargets.VELOCITY)

        # prepare shadow map
        self.framebuffer.set_color_texture(None)
        self.framebuffer.set_depth_texture(shadowmap)
        self.framebuffer.bind_framebuffer()
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.uniformSceneConstants.bind_uniform_block(camera.view,
                                                      np.linalg.inv(camera.view),
                                                      camera.view_origin,
                                                      np.linalg.inv(camera.view_origin),
                                                      camera.projection,
                                                      np.linalg.inv(camera.projection),
                                                      camera.transform.getPos(), FLOAT_ZERO,
                                                      Float4(camera.near, camera.far, 0.0, 0.0))

        light = lights[0]
        # light.transform.setPos((math.sin(timeModule.time()) * 20.0, 0.0, math.cos(timeModule.time()) * 20.0))
        light.transform.updateInverseTransform()  # update view matrix
        self.uniformLightConstants.bind_uniform_block(light.transform.getPos(), FLOAT_ZERO,
                                                      light.transform.front, FLOAT_ZERO,
                                                      light.lightColor)

        # render shadow
        shadow_distance = 50.0 / camera.meter_per_unit
        width, height = shadow_distance * 0.5, shadow_distance * 0.5
        projection = ortho(-width, width, -height, height, -shadow_distance, shadow_distance)

        lightPosMatrix = getTranslateMatrix(*(-camera.transform.getPos()))
        shadow_projection = light.transform.inverse_matrix.copy()
        # shadow_projection[3, 0:3] = light.transform.front * -shadow_distance
        shadow_projection[...] = np.dot(np.dot(lightPosMatrix, shadow_projection), projection)

        glFrontFace(GL_CW)
        self.render_objects(shadow_projection, shadow_projection, True)

        self.framebuffer.set_color_textures([colortexture, diffusetexture, normaltexture, velocity_texture])
        self.framebuffer.set_depth_texture(depthtexture)
        self.framebuffer.bind_framebuffer()
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        view_projection = camera.view_projection
        prev_view_projection = camera.prev_view_projection
        glFrontFace(GL_CCW)
        self.render_objects(view_projection, prev_view_projection, False, True, shadow_projection, shadowmap)

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

    def set_debug_rendertarget(self, rendertarget_index):
        rendertarget_enum = RenderTargets.convert_index_to_enum(rendertarget_index)
        logger.info("Current render target : %s" % str(rendertarget_enum))
        if rendertarget_enum:
            self.debug_rendertarget = self.rendertarget_manager.get_rendertarget(rendertarget_enum)
        else:
            self.debug_rendertarget = None

    def render_objects_begin(self):
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glFrontFace(GL_CCW)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)
        glPolygonMode(GL_FRONT_AND_BACK, self.viewMode)

    def render_objects(self, view_projection, prev_view_projection, cast_shadow=False, render_shadow=False, shadow_projection=None, shadow_texture=None):
        # Test Code : sort list by mesh, material
        static_actors = self.sceneManager.get_static_actors()[:]
        geometries = []
        for static_actor in static_actors:
            geometries += static_actor.geometries
        geometries.sort(key=lambda x: id(x.vertex_buffer))

        # draw static meshes
        default_material_instance = self.resource_manager.getDefaultMaterialInstance()
        last_vertex_buffer = None
        last_material = None
        last_material_instance = None
        last_actor = None
        for geometry in geometries:
            actor = geometry.parent_actor
            actor_has_bone = geometry.skeleton is not None
            if cast_shadow:
                if actor_has_bone:
                    material_instance = self.resource_manager.getMaterialInstance("shadowmap_skeleton")
                else:
                    material_instance = self.resource_manager.getMaterialInstance("shadowmap")
            else:
                material_instance = geometry.material_instance or default_material_instance
            material = material_instance.material if material_instance else None

            if last_material != material and material is not None:
                material.use_program()

            if last_material_instance != material_instance and material_instance is not None:
                material_instance.bind_material_instance()

            # At last, bind buffers
            if geometry is not None and last_vertex_buffer != geometry.vertex_buffer:
                geometry.bind_vertex_buffer()

            if last_actor != actor and material_instance:
                material_instance.bind_uniform_data('view_projection', view_projection)
                material_instance.bind_uniform_data('prev_view_projection', prev_view_projection)
                if render_shadow:
                    material_instance.bind_uniform_data('model', actor.transform.matrix)
                    material_instance.bind_uniform_data('shadow_matrix', shadow_projection)
                    material_instance.bind_uniform_data('shadow_texture', shadow_texture)
                if actor_has_bone:
                    animation_buffer = actor.get_animation_buffer(geometry.skeleton.index)
                    prev_animation_buffer = actor.get_prev_animation_buffer(geometry.skeleton.index)
                    material_instance.bind_uniform_data('bone_matrices', animation_buffer, len(animation_buffer))
                    material_instance.bind_uniform_data('prev_bone_matrices', prev_animation_buffer,
                                                        len(prev_animation_buffer))

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
        static_actors = self.sceneManager.get_static_actors()[:]

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
        glEnable(GL_BLEND)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDisable(GL_LIGHTING)
        glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        camera = self.sceneManager.getMainCamera()
        mesh = self.resource_manager.getMesh("Quad")
        mesh.bind_vertex_buffer()

        backbuffer = self.rendertarget_manager.get_rendertarget(RenderTargets.BACKBUFFER)
        texture_diffuse = self.rendertarget_manager.get_rendertarget(RenderTargets.DIFFUSE)
        texture_normal = self.rendertarget_manager.get_rendertarget(RenderTargets.WORLD_NORMAL)
        texture_depth = self.rendertarget_manager.get_rendertarget(RenderTargets.DEPTHSTENCIL)
        texture_velocity = self.rendertarget_manager.get_rendertarget(RenderTargets.VELOCITY)

        self.framebuffer.set_color_texture(backbuffer)
        self.framebuffer.set_depth_texture(None)
        self.framebuffer.bind_framebuffer()

        self.motion_blur.use_program()
        self.motion_blur.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.motion_blur.bind_uniform_data("texture_velocity", texture_velocity)
        self.motion_blur.bind_material_instance()
        mesh.draw_elements()

        # tonemapping
        # self.tonemapping.use_program()
        # texture_diffuse = self.rendertarget_manager.get_rendertarget(RenderTargets.DIFFUSE)
        # self.tonemapping.set_uniform_data("texture_diffuse", texture_diffuse)
        # self.tonemapping.bind_material_instance()
        # mesh.draw_elements()

        texture_ssr = self.rendertarget_manager.get_rendertarget(RenderTargets.SCREEN_SPACE_REFLECTION)
        self.framebuffer.set_color_texture(texture_ssr)
        self.framebuffer.bind_framebuffer()
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        self.screeen_space_reflection.use_program()
        # self.screeen_space_reflection.bind_uniform_data("viewOriginProj", camera.view_origin_projection)
        # self.screeen_space_reflection.bind_uniform_data("invViewOriginProj", np.linalg.inv(camera.view_origin_projection))
        self.screeen_space_reflection.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.screeen_space_reflection.bind_uniform_data("texture_normal", texture_normal)
        self.screeen_space_reflection.bind_uniform_data("texture_depth", texture_depth)
        self.screeen_space_reflection.bind_material_instance()
        mesh.draw_elements()

        if self.debug_rendertarget and self.debug_rendertarget is not backbuffer:
            self.framebuffer.set_color_texture(backbuffer)
            self.framebuffer.bind_framebuffer()
            self.copy_rendertarget.use_program()
            self.copy_rendertarget.bind_uniform_data("is_depth_texture", self.debug_rendertarget.is_depth_texture())
            self.copy_rendertarget.bind_uniform_data("texture_diffuse", self.debug_rendertarget)
            mesh.draw_elements()
