import random
import time
from ctypes import c_void_p

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from App import CoreManager
from Common import logger, log_level, COMMAND
from Utilities import *
from .RenderTarget import RenderTargets
from .RenderOptions import RenderOption


class JitterMode:
    Uniform2x = np.array([[0.25, 0.75], [0.5, 0.5]], dtype=np.float32) * 2.0 - 1.0
    Hammersley4x = np.array([Hammersley2D(i, 4) for i in range(4)], dtype=np.float32) * 2.0 - 1.0
    Hammersley8x = np.array([Hammersley2D(i, 4) for i in range(4)], dtype=np.float32) * 2.0 - 1.0
    Hammersley16x = np.array([Hammersley2D(i, 4) for i in range(4)], dtype=np.float32) * 2.0 - 1.0


class AntiAliasing(AutoEnum):
    TAA = ()
    MSAA = ()
    SSAA = ()
    NONE_AA = ()
    COUNT = ()


class PostProcess:
    name = 'PostProcess'

    def __init__(self):
        self.core_manager = None
        self.resource_manager = None
        self.renderer = None
        self.rendertarget_manager = None
        self.quad = None
        self.quad_geometry = None

        self.anti_aliasing = AntiAliasing.TAA
        self.msaa_multisample_count = 4

        self.is_render_bloom = True
        self.bloom = None
        self.bloom_highlight = None
        self.bloom_intensity = 1.0
        self.bloom_threshold_min = 0.75
        self.bloom_threshold_max = 1.5
        self.bloom_scale = 1.0

        self.is_render_motion_blur = True
        self.motion_blur = None
        self.motion_blur_scale = 1.0

        self.is_render_ssao = True
        self.ssao = None
        self.ssao_blur_radius = 2.0
        self.ssao_radius_min_max = np.array([0.01, 1.0], dtype=np.float32)
        self.ssao_kernel_size = 32  # Note : ssao.glsl
        self.ssao_kernel = np.zeros((self.ssao_kernel_size, 3), dtype=np.float32)

        self.velocity = None

        self.is_render_ssr = True
        self.screeen_space_reflection = None

        self.is_render_tonemapping = True
        self.exposure = 1.0
        self.tonemapping = None

        self.atmosphere = None
        self.linear_depth = None
        self.blur = None
        self.gaussian_blur = None
        self.deferred_shading = None
        self.copy_texture_mi = None
        self.render_texture_2d = None
        self.render_texture_3d = None
        self.render_texture_cube = None

        self.temporal_antialiasing = None
        self.jitter_mode = JitterMode.Hammersley4x
        self.jitter = Float2()
        self.jitter_prev = Float2()
        self.jitter_frame = 0
        self.jitter_delta = Float2()

        self.is_render_material_instance = False
        self.target_material_instance = None

        self.Attributes = Attributes()

    def initialize(self):
        self.core_manager = CoreManager.instance()
        self.resource_manager = self.core_manager.resource_manager
        self.renderer = self.core_manager.renderer
        self.rendertarget_manager = self.core_manager.rendertarget_manager

        self.quad = self.resource_manager.getMesh("Quad")
        self.quad_geometry = self.quad.get_geometry()

        self.bloom = self.resource_manager.getMaterialInstance("bloom")
        self.bloom_highlight = self.resource_manager.getMaterialInstance("bloom_highlight")

        # SSAO
        self.ssao = self.resource_manager.getMaterialInstance("ssao")
        for i in range(self.ssao_kernel_size):
            scale = float(i) / float(self.ssao_kernel_size)
            scale = min(max(0.1, scale * scale), 1.0)
            self.ssao_kernel[i][0] = random.uniform(-1.0, 1.0)
            self.ssao_kernel[i][1] = random.uniform(0.0, 1.0)
            self.ssao_kernel[i][2] = random.uniform(-1.0, 1.0)
            self.ssao_kernel[i][:] = normalize(self.ssao_kernel[i]) * scale

        self.velocity = self.resource_manager.getMaterialInstance("velocity")

        self.atmosphere = self.resource_manager.getMaterialInstance("atmosphere")
        self.tonemapping = self.resource_manager.getMaterialInstance("tonemapping")
        self.blur = self.resource_manager.getMaterialInstance("blur")
        self.gaussian_blur = self.resource_manager.getMaterialInstance("gaussian_blur")
        self.motion_blur = self.resource_manager.getMaterialInstance("motion_blur")
        self.screeen_space_reflection = self.resource_manager.getMaterialInstance("screen_space_reflection")
        self.linear_depth = self.resource_manager.getMaterialInstance("linear_depth")
        self.deferred_shading = self.resource_manager.getMaterialInstance("deferred_shading")
        self.copy_texture_mi = self.resource_manager.getMaterialInstance("copy_texture")
        self.render_texture_2d = self.resource_manager.getMaterialInstance(name="render_texture_2d",
                                                                           shader_name="render_texture",
                                                                           macros={'GL_TEXTURE_2D': 1})
        self.render_texture_3d = self.resource_manager.getMaterialInstance(name="render_texture_3d",
                                                                           shader_name="render_texture",
                                                                           macros={'GL_TEXTURE_3D': 1})
        self.render_texture_cube = self.resource_manager.getMaterialInstance(name="render_texture_cube",
                                                                             shader_name="render_texture",
                                                                             macros={'GL_TEXTURE_CUBE_MAP': 1})

        # TAA
        self.temporal_antialiasing = self.resource_manager.getMaterialInstance("temporal_antialiasing")

        def get_anti_aliasing_name(anti_aliasing):
            anti_aliasing = str(anti_aliasing)
            return anti_aliasing.split('.')[-1] if '.' in anti_aliasing else anti_aliasing

        anti_aliasing_list = [get_anti_aliasing_name(AntiAliasing.convert_index_to_enum(x)) for x in
                              range(AntiAliasing.COUNT.value)]
        # Send to GUI
        self.core_manager.sendAntiAliasingList(anti_aliasing_list)

    def getAttribute(self):
        self.Attributes.setAttribute('is_render_bloom', self.is_render_bloom)
        self.Attributes.setAttribute('bloom_intensity', self.bloom_intensity)
        self.Attributes.setAttribute('bloom_threshold_min', self.bloom_threshold_min)
        self.Attributes.setAttribute('bloom_threshold_max', self.bloom_threshold_max)
        self.Attributes.setAttribute('bloom_scale', self.bloom_scale)
        self.Attributes.setAttribute('msaa_multisample_count', self.msaa_multisample_count)
        self.Attributes.setAttribute('motion_blur_scale', self.motion_blur_scale)

        self.Attributes.setAttribute('is_render_ssao', self.is_render_ssao)
        self.Attributes.setAttribute('ssao_radius_min_max', self.ssao_radius_min_max)
        self.Attributes.setAttribute('ssao_blur_radius', self.ssao_blur_radius)

        self.Attributes.setAttribute('is_render_ssr', self.is_render_ssr)
        self.Attributes.setAttribute('is_render_motion_blur', self.is_render_motion_blur)

        self.Attributes.setAttribute('is_render_tonemapping', self.is_render_tonemapping)
        self.Attributes.setAttribute('exposure', self.exposure)

        self.Attributes.setAttribute('is_render_material_instance', self.is_render_material_instance)
        self.Attributes.setAttribute('render_material_instance', self.target_material_instance)
        return self.Attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if attributeName == 'msaa_multisample_count':
            self.msaa_multisample_count = attributeValue
            self.set_anti_aliasing(self.anti_aliasing.value, force=True)
        elif attributeName == 'render_material_instance':
            target_material_instance = self.resource_manager.getMaterialInstance(attributeValue)
            if target_material_instance is not None and attributeValue == target_material_instance.name:
                self.target_material_instance = target_material_instance
            else:
                self.target_material_instance = None
        elif hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)

    def set_anti_aliasing(self, index, force=False):
        if index != self.anti_aliasing.value or force:
            old_anti_aliasing = self.anti_aliasing
            self.anti_aliasing = AntiAliasing.convert_index_to_enum(index)
            if self.anti_aliasing in (AntiAliasing.MSAA, AntiAliasing.SSAA) \
                    or old_anti_aliasing in (AntiAliasing.MSAA, AntiAliasing.SSAA):
                self.core_manager.request(COMMAND.RECREATE_RENDER_TARGETS)

    def get_msaa_multisample_count(self):
        if self.anti_aliasing == AntiAliasing.MSAA:
            return self.msaa_multisample_count
        else:
            return 0

    def is_MSAA(self):
        return self.anti_aliasing == AntiAliasing.MSAA

    def enable_MSAA(self):
        return self.anti_aliasing == AntiAliasing.MSAA and 4 <= self.msaa_multisample_count

    def is_SSAA(self):
        return self.anti_aliasing == AntiAliasing.SSAA

    def is_TAA(self):
        return self.anti_aliasing == AntiAliasing.TAA

    def update(self):
        if self.renderer.postprocess.is_TAA():
            self.jitter_frame = (self.jitter_frame + 1) % len(self.jitter_mode)

            # offset of camera projection matrix. NDC Space -1.0 ~ 1.0
            self.jitter_prev[...] = self.jitter
            self.jitter[...] = self.jitter_mode[self.jitter_frame]
            self.jitter[0] /= RenderTargets.TAA_RESOLVE.width
            self.jitter[1] /= RenderTargets.TAA_RESOLVE.height

            # Multiplies by 0.5 because it is in screen coordinate system. 0.0 ~ 1.0
            self.jitter_delta[...] = (self.jitter - self.jitter_prev) * 0.5
        else:
            self.jitter_delta[0] = 0.0
            self.jitter_delta[1] = 0.0
            self.jitter[0] = 0.0
            self.jitter[1] = 0.0

    def bind_quad(self):
        self.quad_geometry.bind_vertex_buffer()

    def render_temporal_antialiasing(self, texture_input, texture_prev, texture_velocity, texture_linear_depth):
        self.temporal_antialiasing.use_program()
        self.temporal_antialiasing.bind_material_instance()
        self.temporal_antialiasing.bind_uniform_data('texture_input', texture_input)
        self.temporal_antialiasing.bind_uniform_data('texture_prev', texture_prev)
        self.temporal_antialiasing.bind_uniform_data('texture_velocity', texture_velocity)
        # self.temporal_antialiasing.bind_uniform_data('texture_depth', texture_linear_depth)
        self.quad_geometry.draw_elements()

    def render_atmosphere(self):
        self.atmosphere.use_program()
        self.atmosphere.bind_material_instance()
        self.atmosphere.bind_uniform_data('texture_linear_depth', RenderTargets.LINEAR_DEPTH)
        self.quad_geometry.draw_elements()

    def render_blur(self, texture_diffuse, blur_kernel_radius=1.0):
        self.blur.use_program()
        self.blur.bind_material_instance()
        self.blur.bind_uniform_data("blur_kernel_radius", blur_kernel_radius)
        self.blur.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.quad_geometry.draw_elements()

    def render_gaussian_blur(self, frame_buffer, texture_target, texture_temp, blur_scale=1.0):
        frame_buffer.set_color_textures(texture_temp)
        frame_buffer.bind_framebuffer()
        glClear(GL_COLOR_BUFFER_BIT)

        self.gaussian_blur.use_program()
        self.gaussian_blur.bind_material_instance()
        self.gaussian_blur.bind_uniform_data("blur_scale", (blur_scale, 0.0))
        self.gaussian_blur.bind_uniform_data("texture_diffuse", texture_target)
        self.quad_geometry.draw_elements()

        frame_buffer.set_color_textures(texture_target)
        frame_buffer.bind_framebuffer()
        glClear(GL_COLOR_BUFFER_BIT)

        self.gaussian_blur.bind_uniform_data("blur_scale", (0.0, blur_scale))
        self.gaussian_blur.bind_uniform_data("texture_diffuse", texture_temp)
        self.quad_geometry.draw_elements()

    def render_motion_blur(self, texture_velocity, texture_diffuse):
        self.motion_blur.use_program()
        self.motion_blur.bind_material_instance()
        motion_blur_scale = self.motion_blur_scale * self.core_manager.delta
        self.motion_blur.bind_uniform_data("motion_blur_scale", motion_blur_scale)
        self.motion_blur.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.motion_blur.bind_uniform_data("texture_velocity", texture_velocity)
        self.quad_geometry.draw_elements()

    def render_bloom(self, frame_buffer, texture_target):
        texture_highlight = self.rendertarget_manager.get_temporary('highlight', texture_target)
        frame_buffer.set_color_textures(texture_highlight)
        frame_buffer.bind_framebuffer()
        glClear(GL_COLOR_BUFFER_BIT)

        self.bloom_highlight.use_program()
        self.bloom_highlight.bind_material_instance()
        self.bloom_highlight.bind_uniform_data('bloom_threshold_min', self.bloom_threshold_min)
        self.bloom_highlight.bind_uniform_data('bloom_threshold_max', self.bloom_threshold_max)
        self.bloom_highlight.bind_uniform_data('texture_diffuse', texture_target)
        self.quad_geometry.draw_elements()

        texture_bloom0 = self.rendertarget_manager.get_temporary('bloom0', texture_target, 1.0 / 2.0)
        texture_bloom1 = self.rendertarget_manager.get_temporary('bloom1', texture_target, 1.0 / 4.0)
        texture_bloom2 = self.rendertarget_manager.get_temporary('bloom2', texture_target, 1.0 / 8.0)
        texture_bloom3 = self.rendertarget_manager.get_temporary('bloom3', texture_target, 1.0 / 16.0)
        texture_bloom0_temp = self.rendertarget_manager.get_temporary('bloom0_temp', texture_target, 1.0 / 2.0)
        texture_bloom1_temp = self.rendertarget_manager.get_temporary('bloom1_temp', texture_target, 1.0 / 4.0)
        texture_bloom2_temp = self.rendertarget_manager.get_temporary('bloom2_temp', texture_target, 1.0 / 8.0)
        texture_bloom3_temp = self.rendertarget_manager.get_temporary('bloom3_temp', texture_target, 1.0 / 16.0)

        bloom_targets = [texture_bloom0, texture_bloom1, texture_bloom2, texture_bloom3]
        temp_bloom_rendertargets = [texture_bloom0_temp, texture_bloom1_temp, texture_bloom2_temp, texture_bloom3_temp]

        def copy_bloom(src, dst):
            frame_buffer.set_color_textures(dst)
            frame_buffer.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)

            self.copy_texture(src)
            self.quad_geometry.draw_elements()

        copy_bloom(texture_highlight, texture_bloom0)
        copy_bloom(texture_bloom0, texture_bloom1)
        copy_bloom(texture_bloom1, texture_bloom2)
        copy_bloom(texture_bloom2, texture_bloom3)

        self.gaussian_blur.use_program()
        self.gaussian_blur.bind_material_instance()
        for i in range(len(bloom_targets)):
            bloom_target = bloom_targets[i]
            temp_bloom_target = temp_bloom_rendertargets[i]

            frame_buffer.set_color_textures(temp_bloom_target)
            frame_buffer.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)

            self.gaussian_blur.bind_uniform_data("blur_scale", (self.bloom_scale, 0.0))
            self.gaussian_blur.bind_uniform_data("texture_diffuse", bloom_target)
            self.quad_geometry.draw_elements()

            frame_buffer.set_color_textures(bloom_target)
            frame_buffer.bind_framebuffer()
            glClear(GL_COLOR_BUFFER_BIT)

            self.gaussian_blur.bind_uniform_data("blur_scale", (0.0, self.bloom_scale))
            self.gaussian_blur.bind_uniform_data("texture_diffuse", temp_bloom_target)
            self.quad_geometry.draw_elements()

        # set additive
        self.renderer.set_blend_state(True, GL_FUNC_ADD, GL_ONE, GL_ONE)

        frame_buffer.set_color_textures(texture_target)
        frame_buffer.bind_framebuffer()

        self.bloom.use_program()
        self.bloom.bind_material_instance()
        self.bloom.bind_uniform_data("bloom_intensity", self.bloom_intensity)
        self.bloom.bind_uniform_data("texture_bloom0", texture_bloom0)
        self.bloom.bind_uniform_data("texture_bloom1", texture_bloom1)
        self.bloom.bind_uniform_data("texture_bloom2", texture_bloom2)
        self.bloom.bind_uniform_data("texture_bloom3", texture_bloom3)
        self.quad_geometry.draw_elements()

        # restore blend state
        self.renderer.restore_blend_state_prev()

    def render_linear_depth(self, texture_depth):
        self.linear_depth.use_program()
        self.linear_depth.bind_material_instance()
        self.linear_depth.bind_uniform_data("texture_depth", texture_depth)
        self.quad_geometry.draw_elements()

    def render_tone_map(self, texture_diffuse):
        self.tonemapping.use_program()
        self.tonemapping.bind_material_instance()
        self.tonemapping.bind_uniform_data("is_render_tonemapping", self.is_render_tonemapping)
        self.tonemapping.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.tonemapping.bind_uniform_data("exposure", self.exposure)
        self.quad_geometry.draw_elements()

    def render_ssao(self, texture_size, isHalfSize, texture_normal, texture_linear_depth):
        self.ssao.use_program()
        self.ssao.bind_material_instance()

        self.ssao.bind_uniform_data("isHalfSize", isHalfSize)
        self.ssao.bind_uniform_data("texture_size", texture_size)
        self.ssao.bind_uniform_data("radius_min_max", self.ssao_radius_min_max)
        self.ssao.bind_uniform_data("kernel", self.ssao_kernel, self.ssao_kernel_size)
        self.ssao.bind_uniform_data("texture_noise", RenderTargets.SSAO_ROTATION_NOISE)
        self.ssao.bind_uniform_data("texture_normal", texture_normal)
        self.ssao.bind_uniform_data("texture_linear_depth", texture_linear_depth)
        self.quad_geometry.draw_elements()

    def render_velocity(self, texture_depth):
        self.velocity.use_program()
        self.velocity.bind_material_instance()
        self.velocity.bind_uniform_data("texture_depth", texture_depth)
        self.quad_geometry.draw_elements()

    def render_screen_space_reflection(self, texture_diffuse, texture_normal, texture_velocity, texture_depth):
        self.screeen_space_reflection.use_program()
        self.screeen_space_reflection.bind_material_instance()
        self.screeen_space_reflection.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.screeen_space_reflection.bind_uniform_data("texture_normal", texture_normal)
        self.screeen_space_reflection.bind_uniform_data("texture_velocity", texture_velocity)
        self.screeen_space_reflection.bind_uniform_data("texture_depth", texture_depth)
        self.quad_geometry.draw_elements()

    def render_deferred_shading(self, texture_probe, atmosphere):
        self.deferred_shading.use_program()
        self.deferred_shading.bind_material_instance()

        self.deferred_shading.bind_uniform_data("texture_diffuse", RenderTargets.DIFFUSE)
        self.deferred_shading.bind_uniform_data("texture_material", RenderTargets.MATERIAL)
        self.deferred_shading.bind_uniform_data("texture_normal", RenderTargets.WORLD_NORMAL)
        self.deferred_shading.bind_uniform_data("texture_depth", RenderTargets.DEPTHSTENCIL)
        self.deferred_shading.bind_uniform_data("texture_shadow", RenderTargets.SHADOWMAP)
        self.deferred_shading.bind_uniform_data("texture_ssao", RenderTargets.SSAO)
        self.deferred_shading.bind_uniform_data("texture_scene_reflect", RenderTargets.SCREEN_SPACE_REFLECTION)
        self.deferred_shading.bind_uniform_data("texture_probe", texture_probe)

        self.deferred_shading.bind_uniform_data("texture_linear_depth", RenderTargets.LINEAR_DEPTH)
        self.deferred_shading.bind_uniform_data("transmittance_texture", atmosphere.transmittance_texture)
        self.deferred_shading.bind_uniform_data("scattering_texture", atmosphere.scattering_texture)
        self.deferred_shading.bind_uniform_data("irradiance_texture", atmosphere.irradiance_texture)
        if atmosphere.optional_single_mie_scattering_texture is not None:
            self.deferred_shading.bind_uniform_data("single_mie_scattering_texture",
                                                    atmosphere.optional_single_mie_scattering_texture)
        self.deferred_shading.bind_uniform_data("SKY_RADIANCE_TO_LUMINANCE", atmosphere.kSky)
        self.deferred_shading.bind_uniform_data("SUN_RADIANCE_TO_LUMINANCE", atmosphere.kSun)
        self.deferred_shading.bind_uniform_data("exposure", atmosphere.exposure)
        self.deferred_shading.bind_uniform_data("earth_center", atmosphere.earth_center)

        self.quad_geometry.draw_elements()

    def copy_texture(self, source_texture):
        self.copy_texture_mi.use_program()
        self.copy_texture_mi.bind_uniform_data("texture_source", source_texture)
        self.quad_geometry.draw_elements()

    def render_texture(self, source_texture):
        if source_texture.target == GL_TEXTURE_3D:
            render_texture_mi = self.render_texture_3d
        elif source_texture.target == GL_TEXTURE_CUBE_MAP:
            render_texture_mi = self.render_texture_cube
        else:
            render_texture_mi = self.render_texture_2d
        render_texture_mi.use_program()
        render_texture_mi.bind_uniform_data("texture_source", source_texture)
        self.quad_geometry.draw_elements()

    def enable_render_material_instance(self):
        return self.is_render_material_instance and self.target_material_instance is not None

    def set_render_material_instance(self, target_material_instance):
        if target_material_instance == self.target_material_instance:
            # off by toggle
            self.is_render_material_instance = False
            self.target_material_instance = None
        else:
            self.is_render_material_instance = True
            self.target_material_instance = target_material_instance

    def render_material_instance(self):
        if self.target_material_instance is not None:
            self.quad_geometry.bind_vertex_buffer()
            self.target_material_instance.use_program()
            self.target_material_instance.bind_material_instance()
            self.quad_geometry.draw_elements()
