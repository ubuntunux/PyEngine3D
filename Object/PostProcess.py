import random
import time
from ctypes import c_void_p

from OpenGL.GL import *
from OpenGL.GLU import *

from App import CoreManager
from Common import logger, log_level, COMMAND
from Utilities import *
from .RenderTarget import RenderTargets


class AntiAliasing(AutoEnum):
    NONE_AA = ()
    MSAA = ()
    SSAA = ()
    COUNT = ()


class PostProcess:
    def __init__(self):
        self.name = 'PostProcess'
        self.core_manager = None
        self.resource_manager = None
        self.renderer = None
        self.rendertarget_manager = None
        self.quad = None
        self.quad_geometry = None

        self.antialiasing = AntiAliasing.NONE_AA
        self.msaa_multisample_count = 4

        self.is_render_bloom = True
        self.bloom = None
        self.bloom_highlight = None
        self.bloom_intensity = 1.0
        self.bloom_threshold_min = 0.75
        self.bloom_threshold_max = 1.5
        self.bloom_scale = 1.0

        self.motion_blur = None
        self.motion_blur_scale = 1.0

        self.is_render_ssao = True
        self.ssao = None
        self.ssao_blur_radius = 2.0
        self.ssao_radius_min_max = np.array([0.01, 1.0], dtype=np.float32)
        self.ssao_kernel_size = 32  # Note : ssao.glsl
        self.ssao_kernel = np.zeros((self.ssao_kernel_size, 3), dtype=np.float32)

        self.tonemapping = None
        self.linear_depth = None
        self.blur = None
        self.gaussian_blur = None
        self.screeen_space_reflection = None
        self.deferred_shading = None
        self.show_rendertarget = None

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

        self.tonemapping = self.resource_manager.getMaterialInstance("tonemapping")
        self.blur = self.resource_manager.getMaterialInstance("blur")
        self.gaussian_blur = self.resource_manager.getMaterialInstance("gaussian_blur")
        self.motion_blur = self.resource_manager.getMaterialInstance("motion_blur")
        self.screeen_space_reflection = self.resource_manager.getMaterialInstance("screen_space_reflection")
        self.linear_depth = self.resource_manager.getMaterialInstance("linear_depth")
        self.deferred_shading = self.resource_manager.getMaterialInstance("deferred_shading")
        self.show_rendertarget = self.resource_manager.getMaterialInstance("show_rendertarget")

        def get_anti_aliasing_name(anti_aliasing):
            anti_aliasing = str(anti_aliasing)
            return anti_aliasing.split('.')[-1] if '.' in anti_aliasing else anti_aliasing

        anti_aliasing_list = [get_anti_aliasing_name(AntiAliasing.convert_index_to_enum(x)) for x in
                              range(AntiAliasing.COUNT.value)]
        # Send to GUI
        self.core_manager.sendAntiAliasingList(anti_aliasing_list)

    def set_anti_aliasing(self, index, force=False):
        if index != self.antialiasing.value or force:
            self.antialiasing = AntiAliasing.convert_index_to_enum(index)
            self.core_manager.request(COMMAND.RECREATE_RENDER_TARGETS)

    def get_msaa_multisample_count(self):
        if self.antialiasing == AntiAliasing.MSAA:
            return self.msaa_multisample_count
        else:
            return 0

    def is_MSAA(self):
        return self.antialiasing == AntiAliasing.MSAA

    def enable_MSAA(self):
        return self.antialiasing == AntiAliasing.MSAA and 4 <= self.msaa_multisample_count

    def is_SSAA(self):
        return self.antialiasing == AntiAliasing.SSAA

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
        return self.Attributes

    def setAttribute(self, attributeName, attributeValue, attribute_index):
        if attributeName == 'msaa_multisample_count':
            self.msaa_multisample_count = attributeValue
            self.set_anti_aliasing(self.antialiasing.value, force=True)
        elif hasattr(self, attributeName):
            setattr(self, attributeName, attributeValue)

    def bind_quad(self):
        self.quad_geometry.bind_vertex_buffer()

    def render_blur(self, texture_diffuse, blur_kernel_radius=1.0):
        self.blur.use_program()
        self.blur.bind_material_instance()
        self.blur.bind_uniform_data("blur_kernel_radius", blur_kernel_radius)
        self.blur.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.quad_geometry.draw_elements()

    def render_gaussian_blur(self, frame_buffer, texture_target, texture_temp, blur_scale=1.0):
        frame_buffer.set_color_texture(texture_temp)
        frame_buffer.bind_framebuffer()

        self.gaussian_blur.use_program()
        self.gaussian_blur.bind_material_instance()
        self.gaussian_blur.bind_uniform_data("blur_scale", (blur_scale, 0.0))
        self.gaussian_blur.bind_uniform_data("texture_diffuse", texture_target)
        self.quad_geometry.draw_elements()

        frame_buffer.set_color_texture(texture_target)
        frame_buffer.bind_framebuffer()

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
        frame_buffer.set_color_texture(texture_highlight)
        frame_buffer.bind_framebuffer()
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
            frame_buffer.set_color_texture(dst)
            frame_buffer.bind_framebuffer()
            self.show_rendertarget.bind_uniform_data("texture_source", src)
            self.quad_geometry.draw_elements()

        self.show_rendertarget.use_program()
        self.show_rendertarget.bind_material_instance()
        self.show_rendertarget.bind_uniform_data("is_depth_texture", False)
        copy_bloom(texture_highlight, texture_bloom0)
        copy_bloom(texture_bloom0, texture_bloom1)
        copy_bloom(texture_bloom1, texture_bloom2)
        copy_bloom(texture_bloom2, texture_bloom3)

        self.gaussian_blur.use_program()
        self.gaussian_blur.bind_material_instance()
        for i in range(len(bloom_targets)):
            bloom_target = bloom_targets[i]
            temp_bloom_target = temp_bloom_rendertargets[i]

            frame_buffer.set_color_texture(temp_bloom_target)
            frame_buffer.bind_framebuffer()
            self.gaussian_blur.bind_uniform_data("blur_scale", (self.bloom_scale, 0.0))
            self.gaussian_blur.bind_uniform_data("texture_diffuse", bloom_target)
            self.quad_geometry.draw_elements()

            frame_buffer.set_color_texture(bloom_target)
            frame_buffer.bind_framebuffer()
            self.gaussian_blur.bind_uniform_data("blur_scale", (0.0, self.bloom_scale))
            self.gaussian_blur.bind_uniform_data("texture_diffuse", temp_bloom_target)
            self.quad_geometry.draw_elements()

        # set additive
        self.renderer.set_blend_state(True, GL_FUNC_ADD, GL_ONE, GL_ONE)

        frame_buffer.set_color_texture(texture_target)
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

    def render_tone_map(self, texture_diffuse, texture_ssao):
        self.tonemapping.use_program()
        self.tonemapping.bind_material_instance()
        self.tonemapping.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.tonemapping.bind_uniform_data("exposure", 1.0)
        self.tonemapping.bind_uniform_data("is_render_ssao", self.is_render_ssao)
        self.tonemapping.bind_uniform_data("texture_ssao", texture_ssao)
        self.quad_geometry.draw_elements()

    def render_ssao(self, framebuffer, texture_ssao, ssao_temp, texture_normal, texture_linear_depth):
        texture_noise = self.rendertarget_manager.get_rendertarget(RenderTargets.SSAO_ROTATION_NOISE)
        framebuffer.set_color_texture(ssao_temp)
        framebuffer.bind_framebuffer()
        self.ssao.use_program()
        self.ssao.bind_material_instance()
        self.ssao.bind_uniform_data("screen_size", [ssao_temp.width, ssao_temp.height])
        self.ssao.bind_uniform_data("radius_min_max", self.ssao_radius_min_max)
        self.ssao.bind_uniform_data("kernel", self.ssao_kernel, self.ssao_kernel_size)
        self.ssao.bind_uniform_data("texture_noise", texture_noise)
        self.ssao.bind_uniform_data("texture_normal", texture_normal)
        self.ssao.bind_uniform_data("texture_linear_depth", texture_linear_depth)
        self.quad_geometry.draw_elements()

        framebuffer.set_color_texture(texture_ssao)
        framebuffer.bind_framebuffer()
        self.render_blur(ssao_temp, blur_kernel_radius=self.ssao_blur_radius)

    def render_screen_space_reflection(self, texture_diffuse, texture_normal, texture_velocity, texture_depth):
        self.screeen_space_reflection.use_program()
        self.screeen_space_reflection.bind_material_instance()
        self.screeen_space_reflection.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.screeen_space_reflection.bind_uniform_data("texture_normal", texture_normal)
        self.screeen_space_reflection.bind_uniform_data("texture_velocity", texture_velocity)
        self.screeen_space_reflection.bind_uniform_data("texture_depth", texture_depth)
        self.quad_geometry.draw_elements()

    def render_deferred_shading(self, texture_diffuse, texture_material, texture_normal, texture_velocity,
                                texture_depth, texture_shadow, texture_scene_reflect, texture_cube):
        self.deferred_shading.use_program()
        self.deferred_shading.bind_material_instance()
        self.deferred_shading.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.deferred_shading.bind_uniform_data("texture_material", texture_material)
        self.deferred_shading.bind_uniform_data("texture_normal", texture_normal)
        self.deferred_shading.bind_uniform_data("texture_velocity", texture_velocity)
        self.deferred_shading.bind_uniform_data("texture_depth", texture_depth)
        self.deferred_shading.bind_uniform_data("texture_shadow", texture_shadow)
        self.deferred_shading.bind_uniform_data("texture_scene_reflect", texture_scene_reflect)
        self.deferred_shading.bind_uniform_data("texture_cube", texture_cube)
        self.quad_geometry.draw_elements()

    def render_copy_rendertarget(self, source_texture):
        self.show_rendertarget.use_program()
        self.show_rendertarget.bind_uniform_data("is_depth_texture", False)
        self.show_rendertarget.bind_uniform_data("texture_source", source_texture)
        self.quad_geometry.draw_elements()
