import math
import random
import time
from ctypes import c_void_p

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from App import CoreManager
from Common import logger, log_level, COMMAND
from OpenGLContext import FrameBufferManager
from Utilities import *
from .Mesh import ScreenQuad
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
        self.framebuffer_manager = None
        self.quad = None

        self.anti_aliasing = AntiAliasing.TAA
        self.msaa_multisample_count = 4

        self.is_render_bloom = True
        self.bloom = None
        self.bloom_highlight = None
        self.bloom_downsampling = None
        self.bloom_intensity = 0.25
        self.bloom_threshold_min = 1.25
        self.bloom_threshold_max = 10.0
        self.bloom_scale = 1.0

        self.is_render_light_shaft = True
        self.light_shaft_intensity = 1.0
        self.light_shaft_threshold = 1.0
        self.light_shaft_length = 1.0
        self.light_shaft = None

        self.is_render_motion_blur = True
        self.motion_blur = None
        self.motion_blur_scale = 1.0

        self.is_render_ssao = True
        self.ssao = None
        self.ssao_blur_radius = 2.0
        self.ssao_radius_min_max = np.array([0.1, 2.0], dtype=np.float32)
        self.ssao_kernel_size = 32  # Note : ssao.glsl
        self.ssao_kernel = np.zeros((self.ssao_kernel_size, 3), dtype=np.float32)
        self.ssao_random_texture = None

        self.velocity = None

        self.is_render_ssr = True
        self.screeen_space_reflection = None

        self.is_render_tonemapping = True
        self.exposure = 1.0
        self.contrast = 1.1
        self.tonemapping = None

        self.linear_depth = None
        self.generate_min_z = None
        self.blur = None
        self.circle_blur = None
        self.gaussian_blur = None
        self.deferred_shading = None
        self.copy_texture_mi = None
        self.render_texture_mi = None

        self.temporal_antialiasing = None
        self.jitter_mode = JitterMode.Hammersley4x
        self.jitter = Float2()
        self.jitter_prev = Float2()
        self.jitter_frame = 0
        self.jitter_delta = Float2()

        self.debug_absolute = False
        self.debug_mipmap = 0.0
        self.debug_intensity_min = 0.0
        self.debug_intensity_max = 1.0

        self.is_render_material_instance = False
        self.target_material_instance = None

        self.Attributes = Attributes()

    def initialize(self):
        self.core_manager = CoreManager.instance()
        self.resource_manager = self.core_manager.resource_manager
        self.renderer = self.core_manager.renderer
        self.rendertarget_manager = self.core_manager.rendertarget_manager
        self.framebuffer_manager = FrameBufferManager.instance()

        self.quad = ScreenQuad.get_vertex_array_buffer()

        self.bloom = self.resource_manager.get_material_instance("bloom")
        self.bloom_highlight = self.resource_manager.get_material_instance("bloom_highlight")
        self.bloom_downsampling = self.resource_manager.get_material_instance("bloom_downsampling")

        # SSAO
        self.ssao = self.resource_manager.get_material_instance("ssao")
        for i in range(self.ssao_kernel_size):
            scale = float(i) / float(self.ssao_kernel_size)
            scale = min(max(0.1, scale * scale), 1.0)
            self.ssao_kernel[i][0] = random.uniform(-1.0, 1.0)
            self.ssao_kernel[i][1] = random.uniform(0.5, 1.0)
            self.ssao_kernel[i][2] = random.uniform(-1.0, 1.0)
            self.ssao_kernel[i][:] = normalize(self.ssao_kernel[i]) * scale
        self.ssao_random_texture = self.resource_manager.get_texture('common.random_normal')

        self.velocity = self.resource_manager.get_material_instance("velocity")

        self.light_shaft = self.resource_manager.get_material_instance("light_shaft")
        self.tonemapping = self.resource_manager.get_material_instance("tonemapping")
        self.blur = self.resource_manager.get_material_instance("blur")
        self.circle_blur = self.resource_manager.get_material_instance("circle_blur")
        self.gaussian_blur = self.resource_manager.get_material_instance("gaussian_blur")
        self.motion_blur = self.resource_manager.get_material_instance("motion_blur")
        self.screeen_space_reflection = self.resource_manager.get_material_instance("screen_space_reflection")
        self.linear_depth = self.resource_manager.get_material_instance("linear_depth")
        self.generate_min_z = self.resource_manager.get_material_instance("generate_min_z")
        self.deferred_shading = self.resource_manager.get_material_instance("deferred_shading")
        self.copy_texture_mi = self.resource_manager.get_material_instance("copy_texture")
        self.render_texture_mi = self.resource_manager.get_material_instance("render_texture")

        # TAA
        self.temporal_antialiasing = self.resource_manager.get_material_instance("temporal_antialiasing")

        def get_anti_aliasing_name(anti_aliasing):
            anti_aliasing = str(anti_aliasing)
            return anti_aliasing.split('.')[-1] if '.' in anti_aliasing else anti_aliasing

        anti_aliasing_list = [get_anti_aliasing_name(AntiAliasing.convert_index_to_enum(x))
                              for x in range(AntiAliasing.COUNT.value)]
        # Send to GUI
        self.core_manager.send_anti_aliasing_list(anti_aliasing_list)

    def get_attribute(self):
        self.Attributes.set_attribute('is_render_bloom', self.is_render_bloom)
        self.Attributes.set_attribute('bloom_intensity', self.bloom_intensity)
        self.Attributes.set_attribute('bloom_threshold_min', self.bloom_threshold_min)
        self.Attributes.set_attribute('bloom_threshold_max', self.bloom_threshold_max)
        self.Attributes.set_attribute('bloom_scale', self.bloom_scale)
        self.Attributes.set_attribute('msaa_multisample_count', self.msaa_multisample_count)
        self.Attributes.set_attribute('motion_blur_scale', self.motion_blur_scale)

        self.Attributes.set_attribute('is_render_ssao', self.is_render_ssao)
        self.Attributes.set_attribute('ssao_radius_min_max', self.ssao_radius_min_max)
        self.Attributes.set_attribute('ssao_blur_radius', self.ssao_blur_radius)

        self.Attributes.set_attribute('is_render_ssr', self.is_render_ssr)
        self.Attributes.set_attribute('is_render_motion_blur', self.is_render_motion_blur)

        self.Attributes.set_attribute('is_render_light_shaft', self.is_render_light_shaft)
        self.Attributes.set_attribute('light_shaft_intensity', self.light_shaft_intensity)
        self.Attributes.set_attribute('light_shaft_threshold', self.light_shaft_threshold)
        self.Attributes.set_attribute('light_shaft_length', self.light_shaft_length)

        self.Attributes.set_attribute('is_render_tonemapping', self.is_render_tonemapping)
        self.Attributes.set_attribute('exposure', self.exposure)
        self.Attributes.set_attribute('contrast', self.contrast)

        self.Attributes.set_attribute('debug_absolute', self.debug_absolute)
        self.Attributes.set_attribute('debug_mipmap', self.debug_mipmap)
        self.Attributes.set_attribute('debug_intensity_min', self.debug_intensity_min)
        self.Attributes.set_attribute('debug_intensity_max', self.debug_intensity_max)

        self.Attributes.set_attribute('is_render_material_instance', self.is_render_material_instance)
        self.Attributes.set_attribute('render_material_instance', self.target_material_instance)
        return self.Attributes

    def set_attribute(self, attribute_name, attribute_value, parent_info, attribute_index):
        if attribute_name == 'msaa_multisample_count':
            self.msaa_multisample_count = attribute_value
            self.set_anti_aliasing(self.anti_aliasing.value, force=True)
        elif attribute_name == 'render_material_instance':
            target_material_instance = self.resource_manager.get_material_instance(attribute_value)
            if target_material_instance is not None and attribute_value == target_material_instance.name:
                self.target_material_instance = target_material_instance
            else:
                self.target_material_instance = None
        elif hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)

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

    def draw_elements(self):
        self.quad.draw_elements()

    def render_temporal_antialiasing(self, texture_input, texture_prev, texture_velocity, texture_linear_depth):
        self.temporal_antialiasing.use_program()
        self.temporal_antialiasing.bind_material_instance()
        self.temporal_antialiasing.bind_uniform_data('texture_input', texture_input)
        self.temporal_antialiasing.bind_uniform_data('texture_prev', texture_prev)
        self.temporal_antialiasing.bind_uniform_data('texture_velocity', texture_velocity)
        # self.temporal_antialiasing.bind_uniform_data('texture_linear_depth', texture_linear_depth)
        self.quad.draw_elements()

    def render_blur(self, texture_diffuse, blur_kernel_radius=1.0):
        self.blur.use_program()
        self.blur.bind_material_instance()
        self.blur.bind_uniform_data("blur_kernel_radius", blur_kernel_radius)
        self.blur.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.quad.draw_elements()

    def render_circle_blur(self, texture_color, loop_count=9, radius=1.0):
        self.circle_blur.use_program()
        self.circle_blur.bind_material_instance()
        self.circle_blur.bind_uniform_data("loop_count", loop_count)
        self.circle_blur.bind_uniform_data("radius", radius)
        self.circle_blur.bind_uniform_data("texture_color", texture_color)
        self.quad.draw_elements()

    def render_gaussian_blur(self, texture_target, texture_temp, blur_scale=1.0):
        self.framebuffer_manager.bind_framebuffer(texture_temp)
        glClear(GL_COLOR_BUFFER_BIT)

        self.gaussian_blur.use_program()
        self.gaussian_blur.bind_material_instance()
        self.gaussian_blur.bind_uniform_data("blur_scale", (blur_scale, 0.0))
        self.gaussian_blur.bind_uniform_data("texture_diffuse", texture_target)
        self.quad.draw_elements()

        self.framebuffer_manager.bind_framebuffer(texture_target)
        glClear(GL_COLOR_BUFFER_BIT)

        self.gaussian_blur.bind_uniform_data("blur_scale", (0.0, blur_scale))
        self.gaussian_blur.bind_uniform_data("texture_diffuse", texture_temp)
        self.quad.draw_elements()

    def render_motion_blur(self, texture_velocity, texture_diffuse):
        self.motion_blur.use_program()
        self.motion_blur.bind_material_instance()
        motion_blur_scale = self.motion_blur_scale * self.core_manager.delta
        self.motion_blur.bind_uniform_data("motion_blur_scale", motion_blur_scale)
        self.motion_blur.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.motion_blur.bind_uniform_data("texture_velocity", texture_velocity)
        self.quad.draw_elements()

    def render_light_shaft(self, texture_diffuse, texture_linear_depth, texture_shadow):
        self.light_shaft.use_program()
        self.light_shaft.bind_material_instance()
        self.light_shaft.bind_uniform_data("light_shaft_intensity", self.light_shaft_intensity)
        self.light_shaft.bind_uniform_data("light_shaft_threshold", self.light_shaft_threshold)
        self.light_shaft.bind_uniform_data("light_shaft_length", self.light_shaft_length)
        self.light_shaft.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.light_shaft.bind_uniform_data("texture_linear_depth", texture_linear_depth)
        self.light_shaft.bind_uniform_data("texture_shadow", texture_shadow)
        self.quad.draw_elements()

    def render_bloom(self, texture_target):
        texture_bloom0 = RenderTargets.BLOOM_0
        texture_bloom1 = RenderTargets.BLOOM_1
        texture_bloom2 = RenderTargets.BLOOM_2
        texture_bloom3 = RenderTargets.BLOOM_3
        texture_bloom4 = RenderTargets.BLOOM_4
        texture_bloom0_temp = self.rendertarget_manager.get_temporary('bloom0_temp', texture_bloom0)
        texture_bloom1_temp = self.rendertarget_manager.get_temporary('bloom1_temp', texture_bloom1)
        texture_bloom2_temp = self.rendertarget_manager.get_temporary('bloom2_temp', texture_bloom2)
        texture_bloom3_temp = self.rendertarget_manager.get_temporary('bloom3_temp', texture_bloom3)
        texture_bloom4_temp = self.rendertarget_manager.get_temporary('bloom4_temp', texture_bloom4)

        self.framebuffer_manager.bind_framebuffer(RenderTargets.BLOOM_0)
        glClear(GL_COLOR_BUFFER_BIT)

        self.bloom_highlight.use_program()
        self.bloom_highlight.bind_material_instance()
        self.bloom_highlight.bind_uniform_data('bloom_threshold_min', self.bloom_threshold_min)
        self.bloom_highlight.bind_uniform_data('bloom_threshold_max', self.bloom_threshold_max)
        self.bloom_highlight.bind_uniform_data('texture_diffuse', texture_target)
        self.quad.draw_elements()

        bloom_targets = [texture_bloom0, texture_bloom1, texture_bloom2, texture_bloom3, texture_bloom4]
        temp_bloom_rendertargets = [texture_bloom0_temp, texture_bloom1_temp, texture_bloom2_temp,
                                    texture_bloom3_temp, texture_bloom4_temp]

        def downsampling(src, dst):
            self.framebuffer_manager.bind_framebuffer(dst)
            glClear(GL_COLOR_BUFFER_BIT)

            self.bloom_downsampling.use_program()
            self.bloom_downsampling.bind_uniform_data("texture_source", src)
            self.quad.draw_elements()

        downsampling(texture_bloom0, texture_bloom1)
        downsampling(texture_bloom1, texture_bloom2)
        downsampling(texture_bloom2, texture_bloom3)
        downsampling(texture_bloom3, texture_bloom4)

        self.gaussian_blur.use_program()
        self.gaussian_blur.bind_material_instance()
        for i in range(len(bloom_targets)):
            bloom_target = bloom_targets[i]
            temp_bloom_target = temp_bloom_rendertargets[i]

            loop = 2
            for j in range(loop):
                self.framebuffer_manager.bind_framebuffer(temp_bloom_target)
                self.gaussian_blur.bind_uniform_data("blur_scale", (self.bloom_scale, 0.0))
                self.gaussian_blur.bind_uniform_data("texture_diffuse", bloom_target)
                self.quad.draw_elements()

                self.framebuffer_manager.bind_framebuffer(bloom_target)
                self.gaussian_blur.bind_uniform_data("blur_scale", (0.0, self.bloom_scale))
                self.gaussian_blur.bind_uniform_data("texture_diffuse", temp_bloom_target)
                self.quad.draw_elements()

    def render_linear_depth(self, texture_depth, texture_linear_depth):
        self.linear_depth.use_program()
        self.linear_depth.bind_material_instance()
        self.linear_depth.bind_uniform_data("texture_depth", texture_depth)
        self.quad.draw_elements()

        self.render_generate_min_z(texture_linear_depth)

    def render_generate_min_z(self, texture_linear_depth):
        lod_count = texture_linear_depth.get_mipmap_count()
        width = texture_linear_depth.width
        height = texture_linear_depth.height

        self.generate_min_z.use_program()

        for lod in range(1, lod_count - 1):
            self.generate_min_z.bind_uniform_data("img_input", texture_linear_depth, level=lod-1, access=GL_READ_ONLY)
            self.generate_min_z.bind_uniform_data("img_output", texture_linear_depth, level=lod, access=GL_WRITE_ONLY)

            width = math.floor(width / 2)
            height = math.floor(height / 2)
            glDispatchCompute(width, height, 1)
            glMemoryBarrier(GL_ALL_BARRIER_BITS)

    def render_tone_map(self, texture_diffuse, texture_bloom0, texture_bloom1, texture_bloom2, texture_bloom3,
                        texture_bloom4, texture_light_shaft):
        self.tonemapping.use_program()
        self.tonemapping.bind_material_instance()
        self.tonemapping.bind_uniform_data("is_render_tonemapping", self.is_render_tonemapping)
        self.tonemapping.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.tonemapping.bind_uniform_data("exposure", self.exposure)
        self.tonemapping.bind_uniform_data("contrast", self.contrast)

        self.tonemapping.bind_uniform_data("is_render_bloom", self.is_render_bloom)
        self.tonemapping.bind_uniform_data("bloom_intensity", self.bloom_intensity)
        self.tonemapping.bind_uniform_data("texture_bloom0", texture_bloom0)
        self.tonemapping.bind_uniform_data("texture_bloom1", texture_bloom1)
        self.tonemapping.bind_uniform_data("texture_bloom2", texture_bloom2)
        self.tonemapping.bind_uniform_data("texture_bloom3", texture_bloom3)
        self.tonemapping.bind_uniform_data("texture_bloom4", texture_bloom4)

        self.tonemapping.bind_uniform_data("is_render_light_shaft", self.is_render_light_shaft)
        self.tonemapping.bind_uniform_data("texture_light_shaft", texture_light_shaft)

        self.quad.draw_elements()

    def render_ssao(self, texture_size, texture_lod, texture_normal, texture_linear_depth):
        self.ssao.use_program()
        self.ssao.bind_material_instance()

        self.ssao.bind_uniform_data("texture_lod", texture_lod)
        self.ssao.bind_uniform_data("texture_size", texture_size)
        self.ssao.bind_uniform_data("radius_min_max", self.ssao_radius_min_max)
        self.ssao.bind_uniform_data("kernel", self.ssao_kernel, num=self.ssao_kernel_size)
        self.ssao.bind_uniform_data("texture_noise", self.ssao_random_texture)
        self.ssao.bind_uniform_data("texture_normal", texture_normal)
        self.ssao.bind_uniform_data("texture_linear_depth", texture_linear_depth)
        self.quad.draw_elements()

    def render_velocity(self, texture_depth):
        self.velocity.use_program()
        self.velocity.bind_material_instance()
        self.velocity.bind_uniform_data("texture_depth", texture_depth)
        self.quad.draw_elements()

    def render_screen_space_reflection(self, texture_diffuse, texture_normal, texture_material, texture_velocity,
                                       texture_depth):
        self.screeen_space_reflection.use_program()
        self.screeen_space_reflection.bind_material_instance()
        texture_random = self.resource_manager.get_texture('common.random')
        self.screeen_space_reflection.bind_uniform_data("texture_random", texture_random)
        self.screeen_space_reflection.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.screeen_space_reflection.bind_uniform_data("texture_normal", texture_normal)
        self.screeen_space_reflection.bind_uniform_data("texture_material", texture_material)
        self.screeen_space_reflection.bind_uniform_data("texture_velocity", texture_velocity)
        self.screeen_space_reflection.bind_uniform_data("texture_depth", texture_depth)
        self.quad.draw_elements()

    def render_deferred_shading(self, texture_probe, atmosphere):
        self.deferred_shading.use_program()
        self.deferred_shading.bind_material_instance()

        self.deferred_shading.bind_uniform_data("texture_diffuse", RenderTargets.DIFFUSE)
        self.deferred_shading.bind_uniform_data("texture_material", RenderTargets.MATERIAL)
        self.deferred_shading.bind_uniform_data("texture_normal", RenderTargets.WORLD_NORMAL)
        self.deferred_shading.bind_uniform_data("texture_depth", RenderTargets.DEPTHSTENCIL)

        self.deferred_shading.bind_uniform_data("texture_probe", texture_probe)
        self.deferred_shading.bind_uniform_data("texture_shadow", RenderTargets.SHADOWMAP)
        self.deferred_shading.bind_uniform_data("texture_ssao", RenderTargets.SSAO)
        self.deferred_shading.bind_uniform_data("texture_scene_reflect", RenderTargets.SCREEN_SPACE_REFLECTION)

        # Bind Atmosphere
        atmosphere.bind_precomputed_atmosphere(self.deferred_shading)

        self.quad.draw_elements()

    def copy_texture(self, source_texture, target_level=0.0):
        self.copy_texture_mi.use_program()
        self.copy_texture_mi.bind_uniform_data("target_level", float(target_level))
        self.copy_texture_mi.bind_uniform_data("texture_source", source_texture)
        self.quad.draw_elements()

    def render_texture(self, source_texture):
        target = source_texture.target
        self.render_texture_mi.use_program()
        self.render_texture_mi.bind_uniform_data("debug_absolute", self.debug_absolute)
        self.render_texture_mi.bind_uniform_data("debug_mipmap", self.debug_mipmap)
        self.render_texture_mi.bind_uniform_data("debug_intensity_min", self.debug_intensity_min)
        self.render_texture_mi.bind_uniform_data("debug_intensity_max", self.debug_intensity_max)
        self.render_texture_mi.bind_uniform_data("debug_target", target)
        self.render_texture_mi.bind_uniform_data("texture_source_2d",
                                                 source_texture if GL_TEXTURE_2D == target else None)
        self.render_texture_mi.bind_uniform_data("texture_source_2d_array",
                                                 source_texture if GL_TEXTURE_2D_ARRAY == target else None)
        self.render_texture_mi.bind_uniform_data("texture_source_3d",
                                                 source_texture if GL_TEXTURE_3D == target else None)
        self.render_texture_mi.bind_uniform_data("texture_source_cube",
                                                 source_texture if GL_TEXTURE_CUBE_MAP == target else None)
        self.quad.draw_elements()

    def is_render_shader(self):
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
            self.target_material_instance.use_program()
            self.target_material_instance.bind_material_instance()
            self.quad.draw_elements()
