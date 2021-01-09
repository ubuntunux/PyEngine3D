import time
import math

from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.shaders import glDeleteShader

import numpy as np

from PyEngine3D.Common import logger
from PyEngine3D.App import CoreManager
from PyEngine3D.Render import ScreenQuad
from PyEngine3D.Utilities import Attributes
from .Constants import *
from .Model import *


class Luminance:
    NONE = 0
    APPROXIMATE = 1
    PRECOMPUTED = 2


class Atmosphere:
    def __init__(self, **object_data):
        self.name = object_data.get('name', 'atmosphere')
        self.attributes = Attributes()
        self.is_render_atmosphere = object_data.get('is_render_atmosphere', True)
        self.use_constant_solar_spectrum = False
        self.use_ozone = True
        self.use_combined_textures = True
        self.luminance_type = Luminance.NONE
        self.num_precomputed_wavelengths = 15 if Luminance.PRECOMPUTED == self.luminance_type else 3
        self.do_white_balance = False
        self.show_help = True
        self.view_distance_meters = 9000.0
        self.view_zenith_angle_radians = 1.47
        self.view_azimuth_angle_radians = -0.1
        self.sun_zenith_angle_radians = 1.3
        self.sun_azimuth_angle_radians = 2.9
        self.sun_direction = Float3()

        self.white_point = Float3()
        self.earth_center = Float3(0.0, -kBottomRadius / kLengthUnitInMeters, 0.0)
        self.sun_size = Float2(math.tan(kSunAngularRadius), math.cos(kSunAngularRadius))

        self.kSky = Float3(1.0, 1.0, 1.0)
        self.kSun = Float3(1.0, 1.0, 1.0)

        self.atmosphere_exposure = 0.0001

        # cloud constants
        self.cloud_exposure = 0.1
        self.cloud_altitude = 100.0
        self.cloud_height = 500.0
        self.cloud_speed = 0.01
        self.cloud_absorption = 0.15

        self.cloud_contrast = 2.0
        self.cloud_coverage = 0.8
        self.cloud_tiling = 0.0004

        self.inscatter_power = 0.25

        self.noise_contrast = 1.0
        self.noise_coverage = 1.0
        self.noise_tiling = 0.0003

        self.model = None
        self.atmosphere_material_instance = None

        self.transmittance_texture = None
        self.scattering_texture = None
        self.irradiance_texture = None
        self.optional_single_mie_scattering_texture = None

        self.cloud_texture = None
        self.noise_texture = None

        self.quad = None

        self.load_data(object_data)

    def get_attribute(self):
        save_data = self.get_save_data()
        attribute_names = list(save_data.keys())
        attribute_names.sort()

        for attribute_name in attribute_names:
            self.attributes.set_attribute(attribute_name, save_data[attribute_name])

        return self.attributes

    def set_attribute(self, attribute_name, attribute_value, item_info_history, attribute_index):
        if hasattr(self, attribute_name):
            setattr(self, attribute_name, attribute_value)

    def load_data(self, object_data):
        for key, value in object_data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_save_data(self):
        save_data = dict(
            is_render_atmosphere=self.is_render_atmosphere,
            atmosphere_exposure=self.atmosphere_exposure,
            cloud_exposure=self.cloud_exposure,
            cloud_altitude=self.cloud_altitude,
            cloud_height=self.cloud_height,
            cloud_tiling=self.cloud_tiling,
            cloud_speed=self.cloud_speed,
            cloud_contrast=self.cloud_contrast,
            cloud_coverage=self.cloud_coverage,
            cloud_absorption=self.cloud_absorption,
            inscatter_power=self.inscatter_power,
            noise_tiling=self.noise_tiling,
            noise_contrast=self.noise_contrast,
            noise_coverage=self.noise_coverage,
            sun_size=self.sun_size,
        )
        return save_data

    def initialize(self):
        resource_manager = CoreManager.instance().resource_manager

        self.quad = ScreenQuad.get_vertex_array_buffer()

        self.atmosphere_material_instance = resource_manager.get_material_instance(
            'precomputed_atmosphere.atmosphere',
            macros={
                'USE_LUMINANCE': 1 if self.luminance_type else 0,
                'COMBINED_SCATTERING_TEXTURES': 1 if self.use_combined_textures else 0
            }
        )

        # precompute constants
        max_sun_zenith_angle = 120.0 / 180.0 * kPi

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

        if Luminance.PRECOMPUTED == self.luminance_type:
            self.kSky[...] = [MAX_LUMINOUS_EFFICACY, MAX_LUMINOUS_EFFICACY, MAX_LUMINOUS_EFFICACY]
        else:
            self.kSky[...] = ComputeSpectralRadianceToLuminanceFactors(wavelengths, solar_irradiance, -3)
        self.kSun[...] = ComputeSpectralRadianceToLuminanceFactors(wavelengths, solar_irradiance, 0)

        # generate precomputed textures
        if not resource_manager.texture_loader.hasResource('precomputed_atmosphere.transmittance') or \
                not resource_manager.texture_loader.hasResource('precomputed_atmosphere.scattering') or \
                not resource_manager.texture_loader.hasResource('precomputed_atmosphere.irradiance') or \
                not resource_manager.texture_loader.hasResource(
                    'precomputed_atmosphere.optional_single_mie_scattering') and not self.use_combined_textures:
            model = Model(wavelengths,
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
                          self.num_precomputed_wavelengths,
                          Luminance.PRECOMPUTED == self.luminance_type,
                          self.use_combined_textures)
            model.generate()

        self.transmittance_texture = resource_manager.get_texture('precomputed_atmosphere.transmittance')
        self.scattering_texture = resource_manager.get_texture('precomputed_atmosphere.scattering')
        self.irradiance_texture = resource_manager.get_texture('precomputed_atmosphere.irradiance')

        if not self.use_combined_textures:
            self.optional_single_mie_scattering_texture = resource_manager.get_texture(
                'precomputed_atmosphere.optional_single_mie_scattering')

        self.cloud_texture = resource_manager.get_texture('precomputed_atmosphere.cloud_3d')
        self.noise_texture = resource_manager.get_texture('precomputed_atmosphere.noise_3d')

    def update(self, main_light):
        if not self.is_render_atmosphere:
            return

        self.sun_direction[...] = main_light.transform.front

    def bind_precomputed_atmosphere(self, material_instance):
        material_instance.bind_uniform_data("transmittance_texture", self.transmittance_texture)
        material_instance.bind_uniform_data("scattering_texture", self.scattering_texture)
        material_instance.bind_uniform_data("irradiance_texture", self.irradiance_texture)

        if not self.use_combined_textures:
            material_instance.bind_uniform_data(
                "single_mie_scattering_texture", self.optional_single_mie_scattering_texture)

        material_instance.bind_uniform_data("SKY_RADIANCE_TO_LUMINANCE", self.kSky * self.atmosphere_exposure)
        material_instance.bind_uniform_data("SUN_RADIANCE_TO_LUMINANCE", self.kSun * self.atmosphere_exposure)

        material_instance.bind_uniform_data("atmosphere_exposure", self.atmosphere_exposure)
        material_instance.bind_uniform_data("earth_center", self.earth_center)

    def bind_cloud(self, material_instance):
        material_instance.bind_uniform_data("texture_cloud", self.cloud_texture)
        material_instance.bind_uniform_data("texture_noise", self.noise_texture)

        material_instance.bind_uniform_data('cloud_exposure', self.cloud_exposure)
        material_instance.bind_uniform_data('cloud_altitude', self.cloud_altitude)
        material_instance.bind_uniform_data('cloud_height', self.cloud_height)
        material_instance.bind_uniform_data('cloud_speed', self.cloud_speed)
        material_instance.bind_uniform_data('cloud_absorption', self.cloud_absorption)

        material_instance.bind_uniform_data('cloud_tiling', self.cloud_tiling)
        material_instance.bind_uniform_data('cloud_contrast', self.cloud_contrast)
        material_instance.bind_uniform_data('cloud_coverage', self.cloud_coverage)

        material_instance.bind_uniform_data('noise_tiling', self.noise_tiling)
        material_instance.bind_uniform_data('noise_contrast', self.noise_contrast)
        material_instance.bind_uniform_data('noise_coverage', self.noise_coverage)

    def render_precomputed_atmosphere(self, texture_linear_depth, texture_shadow, render_light_probe_mode):
        if not self.is_render_atmosphere:
            return

        self.atmosphere_material_instance.use_program()
        self.atmosphere_material_instance.bind_material_instance()
        self.atmosphere_material_instance.bind_uniform_data("texture_linear_depth", texture_linear_depth)
        self.atmosphere_material_instance.bind_uniform_data("texture_shadow", texture_shadow)
        self.atmosphere_material_instance.bind_uniform_data("sun_size", self.sun_size)
        self.atmosphere_material_instance.bind_uniform_data("render_light_probe_mode", render_light_probe_mode)
        self.bind_precomputed_atmosphere(self.atmosphere_material_instance)
        self.bind_cloud(self.atmosphere_material_instance)
        self.quad.draw_elements()
