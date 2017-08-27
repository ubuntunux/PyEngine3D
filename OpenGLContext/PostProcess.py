import time

from OpenGL.GL import *
from OpenGL.GLU import *

from App import CoreManager
from Common import logger, log_level
from Utilities import *
from OpenGLContext import RenderTargets


class PostProcess:
    def __init__(self):
        self.quad = None

        self.tonemapping = None
        self.motion_blur = None
        self.screeen_space_reflection = None
        self.show_rendertarget = None

    def initialize(self):
        core_manager = CoreManager.instance()
        resource_manager = core_manager.resource_manager

        self.quad = resource_manager.getMesh("Quad")

        self.tonemapping = resource_manager.getMaterialInstance("tonemapping")
        self.motion_blur = resource_manager.getMaterialInstance("motion_blur")
        self.screeen_space_reflection = resource_manager.getMaterialInstance("screen_space_reflection")
        self.show_rendertarget = resource_manager.getMaterialInstance("show_rendertarget")

    def set_render_state(self):
        glEnable(GL_BLEND)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDisable(GL_LIGHTING)
        glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def bind_quad(self):
        self.quad.bind_vertex_buffer()

    def render_motion_blur(self, texture_diffuse, texture_velocity):
        self.motion_blur.use_program()
        self.motion_blur.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.motion_blur.bind_uniform_data("texture_velocity", texture_velocity)
        self.motion_blur.bind_material_instance()
        self.quad.draw_elements()

    def render_tone_map(self, texture_diffuse):
        self.tonemapping.use_program()
        self.tonemapping.set_uniform_data("texture_diffuse", texture_diffuse)
        self.tonemapping.bind_material_instance()
        self.quad.draw_elements()

    def render_screen_space_reflection(self, texture_diffuse, texture_normal, texture_depth):
        self.screeen_space_reflection.use_program()
        self.screeen_space_reflection.bind_uniform_data("texture_diffuse", texture_diffuse)
        self.screeen_space_reflection.bind_uniform_data("texture_normal", texture_normal)
        self.screeen_space_reflection.bind_uniform_data("texture_depth", texture_depth)
        self.screeen_space_reflection.bind_material_instance()
        self.quad.draw_elements()

    def render_show_rendertarget(self, source_texture):
        self.show_rendertarget.use_program()
        self.show_rendertarget.bind_uniform_data("is_depth_texture", source_texture.is_depth_texture())
        self.show_rendertarget.bind_uniform_data("texture_source", source_texture)
        self.quad.draw_elements()

