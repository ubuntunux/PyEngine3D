import math

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader

import numpy as np

from Common import logger
from App import CoreManager
from OpenGLContext import VertexArrayBuffer

from .constants import *
from .model import *


class Luminance:
    NONE = 0
    APPROXIMATE = 1
    PRECOMPUTED = 2


class Atmosphere:
    def __init__(self):
        self.use_constant_solar_spectrum = False
        self.use_ozone = True
        self.use_combined_textures = True
        self.use_half_precision = True
        self.use_luminance = None
        self.do_white_balance = False
        self.show_help = True
        self.view_distance_meters = 9000.0
        self.view_zenith_angle_radians = 1.47
        self.view_azimuth_angle_radians = -0.1
        self.sun_zenith_angle_radians = 1.3
        self.sun_azimuth_angle_radians = 2.9
        self.exposure = 10.0

        self.model = None
        self.program = -1

        self.quad = None
        self.atmosphere_shader = None
        self.atmosphere_material_instance = None

        self.InitModel()

    def update(self):
        pass

    def InitModel(self):
        resource_manager = CoreManager.instance().resource_manager

        positions = np.array([(-1, -1, 0, 1), (1, -1, 0, 1), (-1, 1, 0, 1), (1, 1, 0, 1)], dtype=np.float32)
        indices = np.array([0, 1, 2, 2, 1, 3], dtype=np.uint32)

        self.quad = VertexArrayBuffer(
            name='atmosphere quad',
            datas=[positions, ],
            index_data=indices,
            dtype=np.float32
        )

        self.atmosphere_shader = resource_manager.getShader('precomputed_scattering.atmosphere')
        self.atmosphere_material_instance = resource_manager.getMaterialInstance('precomputed_scattering.atmosphere',
                                                                                 macros={'USE_LUMINANCE': 1})

        max_sun_zenith_angle = (102.0 if self.use_half_precision else 120.0) / 180.0 * kPi

        rayleigh_layer = DensityProfileLayer(0.0, 1.0, -1.0 / kRayleighScaleHeight, 0.0, 0.0)
        mie_layer = DensityProfileLayer(0.0, 1.0, -1.0 / kMieScaleHeight, 0.0, 0.0)

        ozone_density = [DensityProfileLayer(25000.0, 0.0, 0.0, 1.0 / 15000.0, -2.0 / 3.0),
                         DensityProfileLayer(0.0, 0.0, 0.0, -1.0 / 15000.0, 8.0 / 3.0)]

        wavelengths = []
        solar_irradiance = []
        rayleigh_scattering = []
        mie_scattering = []
        mie_extinction = []
        absorption_extinction = []
        ground_albedo = []

        for i in range(kLambdaMin, kLambdaMax + 1, 10):
            L = float(i) * 1e-3  # micro-meters
            mie = kMieAngstromBeta / kMieScaleHeight * math.pow(L, -kMieAngstromAlpha)
            wavelengths.append(i)
            if self.use_constant_solar_spectrum:
                solar_irradiance.append(kConstantSolarIrradiance)
            else:
                solar_irradiance.append(kSolarIrradiance[int((i - kLambdaMin) / 10)])
            rayleigh_scattering.append(kRayleigh * math.pow(L, -4))
            mie_scattering.append(mie * kMieSingleScatteringAlbedo)
            mie_extinction.append(mie)
            if self.use_ozone:
                absorption_extinction.append(kMaxOzoneNumberDensity * kOzoneCrossSection[int((i - kLambdaMin) / 10)])
            else:
                absorption_extinction.append(0.0)
            ground_albedo.append(kGroundAlbedo)

        rayleigh_density = [rayleigh_layer, ]
        mie_density = [mie_layer, ]
        num_precomputed_wavelengths = 15 if self.use_luminance == Luminance.PRECOMPUTED else 3

        definitions_glsl = resource_manager.getShader('precomputed_scattering.definitions').shader_code
        functions_glsl = resource_manager.getShader('precomputed_scattering.functions').shader_code

        self.model = Model(wavelengths,
                           solar_irradiance,
                           kSunAngularRadius,
                           kBottomRadius,
                           kTopRadius,
                           rayleigh_density,
                           rayleigh_scattering,
                           mie_density,
                           mie_scattering,
                           mie_extinction,
                           kMiePhaseFunctionG,
                           ozone_density,
                           absorption_extinction,
                           ground_albedo,
                           max_sun_zenith_angle,
                           kLengthUnitInMeters,
                           num_precomputed_wavelengths,
                           self.use_combined_textures,
                           self.use_half_precision,
                           definitions_glsl,
                           functions_glsl)
        # self.model.Init()

        return

        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        vertex_shader_source = kDemoVertexShader
        glShaderSource(vertex_shader, vertex_shader_source)
        glCompileShader(vertex_shader)

        fragment_shader_source = ""
        if self.use_luminance != NONE:
            fragment_shader_source += "#define USE_LUMINANCE\n"
        fragment_shader_source += demo_glsl

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_shader_source)
        glCompileShader(fragment_shader)

        self.program = glCreateProgram()
        glAttachShader(self.program, vertex_shader)
        glAttachShader(self.program, fragment_shader)
        glAttachShader(self.program, model.GetShader())
        glLinkProgram(self.program)
        glDetachShader(self.program, vertex_shader)
        glDetachShader(self.program, fragment_shader)
        glDetachShader(self.program, model.GetShader())
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        glUseProgram(self.program)
        self.model.SetProgramUniforms(self.program, 0, 1, 2, 3)
        if self.do_white_balance:
            white_point_r, white_point_g, white_point_b = ConvertSpectrumToLinearSrgb(wavelengths, solar_irradiance)
        white_point = (white_point_r + white_point_g + white_point_b) / 3.0
        white_point_r /= white_point
        white_point_g /= white_point
        white_point_b /= white_point

        location = glGetUniformLocation(self.program, "white_point")
        glUniform3f(location, [white_point_r, white_point_g, white_point_b])
        location = glGetUniformLocation(self.program, "earth_center")
        glUniform3f(location, [0.0, 0.0, -kBottomRadius / kLengthUnitInMeters])
        location = glGetUniformLocation(self.program, "sun_size")
        glUniform2f(location, [tan(kSunAngularRadius), cos(kSunAngularRadius)])

        # This sets 'view_from_clip', which only depends on the window size.
        viewport_width, viewport_height = glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT)
        glViewport(0, 0, viewport_width, viewport_height)

        kFovY = 50.0 / 180.0 * kPi
        kTanFovY = tan(kFovY / 2.0)
        aspect_ratio = float(viewport_width) / float(viewport_height)

        view_from_clip = np.array([[kTanFovY * aspect_ratio, 0.0, 0.0, 0.0],
                                   [0.0, kTanFovY, 0.0, 0.0],
                                   [0.0, 0.0, 0.0, -1.0],
                                   [0.0, 0.0, 1.0, 1.0]], dtype=np.float32)

        glUniformMatrix4fv(glGetUniformLocation(self.program, "view_from_clip"), 1, GL_TRUE, view_from_clip)

    def render_precomputed_atmosphere(self, main_camera):
        self.quad.bind_vertex_buffer()
        self.atmosphere_material_instance.use_program()

        view_zenith_angle_radians = 0.0
        view_azimuth_angle_radians = 0.0

        cos_z = math.cos(view_zenith_angle_radians)
        sin_z = math.sin(view_zenith_angle_radians)
        cos_a = math.cos(view_azimuth_angle_radians)
        sin_a = math.sin(view_azimuth_angle_radians)
        ux = np.array([-sin_a, cos_a, 0.0], np.float32)
        uy = np.array([-cos_z * cos_a, -cos_z * sin_a, sin_z], np.float32)
        uz = np.array([sin_z * cos_a, sin_z * sin_a, cos_z], np.float32)
        l = self.view_distance_meters / kLengthUnitInMeters

        model_from_view = main_camera.view_origin.copy()
        model_from_view[3][0] = model_from_view[2][0] * l
        model_from_view[3][1] = model_from_view[2][1] * l
        model_from_view[3][2] = model_from_view[2][2] * l

        kFovY = 50.0 / 180.0 * kPi
        kTanFovY = math.tan(kFovY / 2.0)
        view_from_clip = np.array([[kTanFovY * main_camera.aspect, 0.0, 0.0, 0.0],
                                   [0.0, kTanFovY, 0.0, 0.0],
                                   [0.0, 0.0, 0.0, -1.0],
                                   [0.0, 0.0, 1.0, 1.0]], dtype=np.float32)

        self.atmosphere_material_instance.bind_uniform_data("model_from_view", model_from_view)
        self.atmosphere_material_instance.bind_uniform_data("view_from_clip", view_from_clip)

        self.quad.draw_elements()

    def HandleRedisplayEvent(self):
        cos_z = cos(view_zenith_angle_radians)
        sin_z = sin(view_zenith_angle_radians)
        cos_a = cos(view_azimuth_angle_radians)
        sin_a = sin(view_azimuth_angle_radians)
        ux = np.array([-sin_a, cos_a, 0.0], np.float32)
        uy = np.array([-cos_z * cos_a, -cos_z * sin_a, sin_z], np.float32)
        uz = np.array([sin_z * cos_a, sin_z * sin_a, cos_z], np.float32)
        l = self.view_distance_meters / kLengthUnitInMeters

        model_from_view = np.array(
            [[ux[0], uy[0], uz[0], uz[0] * l],
             [ux[1], uy[1], uz[1], uz[1] * l],
             [ux[2], uy[2], uz[2], uz[2] * l],
             [0.0, 0.0, 0.0, 1.0]], np.float32)

        location = glGetUniformLocation(self.program, "camera")
        glUniform3f(location, uz * l)

        location = glGetUniformLocation(self.program, "exposure")
        glUniform1f(location, (self.exposure * 1e-5) if self.use_luminance != Luminance.NONE else self.exposure)

        location = glGetUniformLocation(self.program_, "model_from_view")
        glUniformMatrix4fv(location, 1, GL_TRUE, model_from_view)

        sun_direction = np.array(
            [cos(sun_azimuth_angle_radians) * sin(sun_zenith_angle_radians),
             sin(sun_azimuth_angle_radians) * sin(sun_zenith_angle_radians),
             cos(sun_zenith_angle_radians)], dtype=np.float32)
        location = glGetUniformLocation(self.program, "sun_direction")
        glUniform3f(location, sun_direction)

        glBindVertexArray(full_screen_quad_vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)

        glutSwapBuffers()
        glutPostRedisplay()

    def SetView(self,
                view_distance_meters,
                view_zenith_angle_radians,
                view_azimuth_angle_radians,
                sun_zenith_angle_radians,
                sun_azimuth_angle_radians,
                exposure):
        self.view_distance_meters = view_distance_meters
        self.view_zenith_angle_radians = view_zenith_angle_radians
        self.view_azimuth_angle_radians = view_azimuth_angle_radians
        self.sun_zenith_angle_radians = sun_zenith_angle_radians
        self.sun_azimuth_angle_radians = sun_azimuth_angle_radians
        self.exposure = exposure
