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
from . import SkeletonActor, StaticActor, DebugLine


class Renderer_Basic(Singleton):
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

        self.debug_lines_2d = []
        self.debug_lines_3d = []

    def initialize(self, core_manager):
        logger.info("Initialize Renderer")
        self.core_manager = core_manager
        self.viewport_manager = core_manager.viewport_manager
        self.viewport = self.viewport_manager.main_viewport
        self.resource_manager = core_manager.resource_manager
        self.render_option_manager = core_manager.render_option_manager
        self.scene_manager = core_manager.scene_manager
        self.debug_line_manager = core_manager.debug_line_manager
        self.postprocess = PostProcess()
        self.postprocess.initialize()

        self.uniform_point_light_data = np.zeros(MAX_POINT_LIGHTS, dtype=[('color', np.float32, 3),
                                                                          ('radius', np.float32, 1),
                                                                          ('pos', np.float32, 3),
                                                                          ('render', np.float32, 1)])

        self.initialized = True

        # Send to GUI
        # self.core_manager.send_rendering_type_list(rendering_type_list)

    def close(self):
        pass

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
        pass

    def render_light_probe(self, light_probe):
        pass

    def render_actors(self, render_group, render_infos):
        if len(render_infos) < 1:
            return

        vertex_normal = Float3(0.0, 0.0, 0.0)
        position = Float4(0.0, 0.0, 0.0)

        for render_info in render_infos:
            actor = render_info.actor
            geometry = render_info.geometry
            geometry_data = render_info.geometry_data
            gl_call_list = render_info.gl_call_list
            material_instance = render_info.material_instance
            indices = geometry_data['indices']
            positions = geometry_data['positions']
            normals = geometry_data['normals']
            texcoords = geometry_data['texcoords']
            bone_indicies = geometry_data.get('bone_indicies', [])
            bone_weights = geometry_data.get('bone_weights', [])

            if RenderGroup.SKELETON_ACTOR == render_group:
                animation_buffer = actor.get_animation_buffer(geometry.skeleton.index)
            else:
                animation_buffer = None

            glPushMatrix()

            glTranslatef(*actor.transform.get_pos())
            glRotatef(radian_to_degree(actor.transform.get_yaw()), 0.0, 1.0, 0.0)
            glRotatef(radian_to_degree(actor.transform.get_roll()), 0.0, 0.0, 1.0)
            glRotatef(radian_to_degree(actor.transform.get_pitch()), 1.0, 0.0, 0.0)
            glScalef(*actor.transform.get_scale())

            if material_instance is not None:
                mat_a = [0.2, 0.2, 0.2, 1.0]
                mat_d = [1.0, 1.0, 1.0, 1.0]
                mat_s = [1.0, 1.0, 1.0, 1.0]
                low_sh = [60.0]
                glMaterialfv(GL_FRONT, GL_AMBIENT, mat_a)
                glMaterialfv(GL_FRONT, GL_DIFFUSE, mat_d)
                glMaterialfv(GL_FRONT, GL_SPECULAR, mat_s)
                glMaterialfv(GL_FRONT, GL_SHININESS, low_sh)

            if animation_buffer is not None:
                glBegin(GL_TRIANGLES)
                for index in indices:
                    vertex_normal[:] = 0.0
                    position[:] = 0.0
                    for n, bone_index in enumerate(bone_indicies[index]):
                        bone_weight = bone_weights[bone_index][n]
                        position += np.dot([*positions[index][0:3], 1.0], animation_buffer[bone_index] * bone_weight)
                        vertex_normal += np.dot([*normals[index][0:3], 0.0], animation_buffer[bone_index] * bone_weight)[:3]
                    glTexCoord2f(*texcoords[index])
                    glNormal3f(*vertex_normal)
                    glVertex3f(*(position[0:3] / position[3]))
                glEnd()
            else:
                glCallList(gl_call_list)

            glPopMatrix()

    def render_log(self):
        pass

    def render_text(self, text_render_data, offset_x, offset_y, canvas_width, canvas_height):
        pass

    def light_setup(self):
        glEnable(GL_LIGHTING)

        ambient_light = [0.1, 0.1, 0.1, 1.0]
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, ambient_light)

        light_ambient = [0.1, 0.1, 0.1, 1.0]
        light_diffuse = [1.0, 1.0, 1.0, 1.0]
        light_specular = [1.0, 1.0, 1.0, 1.0]
        light_direction = [2.0, 2.0, 2.0, 0.0]
        light_position = [2.0, 2.0, 2.0, 1.0]

        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)
        glLightfv(GL_LIGHT0, GL_POSITION, light_direction)  # directional light
        # glLightfv(GL_LIGHT0, GL_POSITION, light_position)  # point light

    def render_scene(self):
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glPolygonMode(GL_FRONT_AND_BACK, self.view_mode)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_CULL_FACE)
        glEnable(GL_NORMALIZE)
        glFrontFace(GL_CCW)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glDepthMask(True)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glViewport(0, 0, self.viewport.width, self.viewport.height)

        self.set_blend_state(False)

        self.light_setup()

        glPushMatrix()
        self.perspective_view(look_at=True)

        self.render_actors(RenderGroup.STATIC_ACTOR, self.scene_manager.static_solid_render_infos)
        self.render_actors(RenderGroup.SKELETON_ACTOR, self.scene_manager.skeleton_solid_render_infos)

        glPopMatrix()

        # draw line
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        self.debug_line_manager.render_debug_lines()
