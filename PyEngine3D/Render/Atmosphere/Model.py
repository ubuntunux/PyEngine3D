from math import cos, sin
import numpy as np

from OpenGL.GL import *

from PyEngine3D.Utilities import *
from PyEngine3D.App import CoreManager
from PyEngine3D.OpenGLContext import CreateTexture, Texture2D, Texture3D, FrameBuffer
from PyEngine3D.Render import ScreenQuad

from .Constants import *


def CieColorMatchingFunctionTableValue(wavelength, column):
    if wavelength <= kLambdaMin or wavelength >= kLambdaMax:
        return 0.0

    u = (wavelength - kLambdaMin) / 5.0
    row = int(u)
    assert(row >= 0 and row + 1 < 95)
    assert(CIE_2_DEG_COLOR_MATCHING_FUNCTIONS[4 * row] <= wavelength <= CIE_2_DEG_COLOR_MATCHING_FUNCTIONS[4 * (row + 1)])

    u -= row
    return CIE_2_DEG_COLOR_MATCHING_FUNCTIONS[4 * row + column] * (1.0 - u) + \
        CIE_2_DEG_COLOR_MATCHING_FUNCTIONS[4 * (row + 1) + column] * u


def Interpolate(wavelengths, wavelength_function, wavelength):
    assert(len(wavelength_function) == len(wavelengths))
    if wavelength < wavelengths[0]:
        return wavelength_function[0]

    for i in range(len(wavelengths) - 1):
        if wavelength < wavelengths[i + 1]:
            u = (wavelength - wavelengths[i]) / (wavelengths[i + 1] - wavelengths[i])
            return wavelength_function[i] * (1.0 - u) + wavelength_function[i + 1] * u
    return wavelength_function[wavelength_function.size() - 1]


# The returned constants are in lumen.nm / watt.
def ComputeSpectralRadianceToLuminanceFactors(wavelengths, solar_irradiance, lambda_power):
    k_r = 0.0
    k_g = 0.0
    k_b = 0.0

    solar_r = Interpolate(wavelengths, solar_irradiance, kLambdaR)
    solar_g = Interpolate(wavelengths, solar_irradiance, kLambdaG)
    solar_b = Interpolate(wavelengths, solar_irradiance, kLambdaB)
    dlambda = 1

    for L in range(kLambdaMin, kLambdaMax, dlambda):
        x_bar = CieColorMatchingFunctionTableValue(L, 1)
        y_bar = CieColorMatchingFunctionTableValue(L, 2)
        z_bar = CieColorMatchingFunctionTableValue(L, 3)
        r_bar = XYZ_TO_SRGB[0] * x_bar + XYZ_TO_SRGB[1] * y_bar + XYZ_TO_SRGB[2] * z_bar
        g_bar = XYZ_TO_SRGB[3] * x_bar + XYZ_TO_SRGB[4] * y_bar + XYZ_TO_SRGB[5] * z_bar
        b_bar = XYZ_TO_SRGB[6] * x_bar + XYZ_TO_SRGB[7] * y_bar + XYZ_TO_SRGB[8] * z_bar
        irradiance = Interpolate(wavelengths, solar_irradiance, L)
        k_r += r_bar * irradiance / solar_r * pow(L / kLambdaR, lambda_power)
        k_g += g_bar * irradiance / solar_g * pow(L / kLambdaG, lambda_power)
        k_b += b_bar * irradiance / solar_b * pow(L / kLambdaB, lambda_power)
    k_r *= MAX_LUMINOUS_EFFICACY * dlambda
    k_g *= MAX_LUMINOUS_EFFICACY * dlambda
    k_b *= MAX_LUMINOUS_EFFICACY * dlambda
    return [k_r, k_g, k_b]


def ConvertSpectrumToLinearSrgb(wavelengths, spectrum):
    x = 0.0
    y = 0.0
    z = 0.0
    dlambda = 1
    for L in range(kLambdaMin, kLambdaMax, dlambda):
        value = Interpolate(wavelengths, spectrum, L)
        x += CieColorMatchingFunctionTableValue(L, 1) * value
        y += CieColorMatchingFunctionTableValue(L, 2) * value
        z += CieColorMatchingFunctionTableValue(L, 3) * value

    r = MAX_LUMINOUS_EFFICACY * (XYZ_TO_SRGB[0] * x + XYZ_TO_SRGB[1] * y + XYZ_TO_SRGB[2] * z) * dlambda
    g = MAX_LUMINOUS_EFFICACY * (XYZ_TO_SRGB[3] * x + XYZ_TO_SRGB[4] * y + XYZ_TO_SRGB[5] * z) * dlambda
    b = MAX_LUMINOUS_EFFICACY * (XYZ_TO_SRGB[6] * x + XYZ_TO_SRGB[7] * y + XYZ_TO_SRGB[8] * z) * dlambda
    return r, g, b


class DensityProfileLayer:
    def __init__(self, width=0.0, exp_term=0.0, exp_scale=0.0, linear_term=0.0, constant_term=0.0):
        self.width = width
        self.exp_term = exp_term
        self.exp_scale = exp_scale
        self.linear_term = linear_term
        self.constant_term = constant_term


class Model:
    def __init__(self,
                 wavelengths,
                 solar_irradiance,
                 sun_angular_radius,
                 bottom_radius,
                 top_radius,
                 rayleigh_density,
                 rayleigh_scattering,
                 mie_density,
                 mie_scattering,
                 mie_extinction,
                 mie_phase_function_g,
                 absorption_density,
                 absorption_extinction,
                 ground_albedo,
                 max_sun_zenith_angle,
                 length_unit_in_meters,
                 num_precomputed_wavelengths,
                 precompute_illuminance,
                 use_combined_textures):

        self.wavelengths = wavelengths
        self.solar_irradiance = solar_irradiance
        self.sun_angular_radius = sun_angular_radius
        self.bottom_radius = bottom_radius
        self.top_radius = top_radius
        self.rayleigh_density = rayleigh_density
        self.rayleigh_scattering = rayleigh_scattering
        self.mie_density = mie_density
        self.mie_scattering = mie_scattering
        self.mie_extinction = mie_extinction
        self.mie_phase_function_g = mie_phase_function_g
        self.absorption_density = absorption_density
        self.absorption_extinction = absorption_extinction
        self.ground_albedo = ground_albedo
        self.max_sun_zenith_angle = max_sun_zenith_angle
        self.length_unit_in_meters = length_unit_in_meters
        self.num_precomputed_wavelengths = num_precomputed_wavelengths
        self.precompute_illuminance = precompute_illuminance
        self.use_combined_textures = use_combined_textures

        self.material_instance_macros = {
            'COMBINED_SCATTERING_TEXTURES': 1 if use_combined_textures else 0
        }

        # Atmosphere shader code
        resource_manager = CoreManager.instance().resource_manager
        shaderLoader = resource_manager.shader_loader
        shader_name = 'precomputed_atmosphere.atmosphere_predefine'
        recompute_atmosphere_predefine = resource_manager.get_shader(shader_name)
        recompute_atmosphere_predefine.shader_code = self.glsl_header_factory([kLambdaR, kLambdaG, kLambdaB])
        shaderLoader.save_resource(shader_name)
        shaderLoader.load_resource(shader_name)

        self.transmittance_texture = CreateTexture(
            name="precomputed_atmosphere.transmittance",
            texture_type=Texture2D,
            width=TRANSMITTANCE_TEXTURE_WIDTH,
            height=TRANSMITTANCE_TEXTURE_HEIGHT,
            internal_format=GL_RGBA32F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_CLAMP_TO_EDGE
        )

        self.scattering_texture = CreateTexture(
            name="precomputed_atmosphere.scattering",
            texture_type=Texture3D,
            width=SCATTERING_TEXTURE_WIDTH,
            height=SCATTERING_TEXTURE_HEIGHT,
            depth=SCATTERING_TEXTURE_DEPTH,
            internal_format=GL_RGBA32F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_CLAMP_TO_EDGE
        )

        self.irradiance_texture = CreateTexture(
            name="precomputed_atmosphere.irradiance",
            texture_type=Texture2D,
            width=IRRADIANCE_TEXTURE_WIDTH,
            height=IRRADIANCE_TEXTURE_HEIGHT,
            internal_format=GL_RGBA32F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_CLAMP
        )

        self.optional_single_mie_scattering_texture = None
        if not self.use_combined_textures:
            self.optional_single_mie_scattering_texture = CreateTexture(
                name="precomputed_atmosphere.optional_single_mie_scattering_texture",
                texture_type=Texture3D,
                width=SCATTERING_TEXTURE_WIDTH,
                height=SCATTERING_TEXTURE_HEIGHT,
                depth=SCATTERING_TEXTURE_DEPTH,
                internal_format=GL_RGBA32F,
                texture_format=GL_RGBA,
                min_filter=GL_LINEAR,
                mag_filter=GL_LINEAR,
                data_type=GL_FLOAT,
                wrap=GL_CLAMP
            )

        self.delta_irradiance_texture = CreateTexture(
            name="precomputed_atmosphere.delta_irradiance_texture",
            texture_type=Texture2D,
            width=IRRADIANCE_TEXTURE_WIDTH,
            height=IRRADIANCE_TEXTURE_HEIGHT,
            internal_format=GL_RGBA32F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_CLAMP
        )

        self.delta_rayleigh_scattering_texture = CreateTexture(
            name="precomputed_atmosphere.delta_rayleigh_scattering_texture",
            texture_type=Texture3D,
            width=SCATTERING_TEXTURE_WIDTH,
            height=SCATTERING_TEXTURE_HEIGHT,
            depth=SCATTERING_TEXTURE_DEPTH,
            internal_format=GL_RGBA32F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_CLAMP
        )

        self.delta_mie_scattering_texture = CreateTexture(
            name="precomputed_atmosphere.delta_mie_scattering_texture",
            texture_type=Texture3D,
            width=SCATTERING_TEXTURE_WIDTH,
            height=SCATTERING_TEXTURE_HEIGHT,
            depth=SCATTERING_TEXTURE_DEPTH,
            internal_format=GL_RGBA32F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_CLAMP
        )

        self.delta_scattering_density_texture = CreateTexture(
            name="precomputed_atmosphere.delta_scattering_density_texture",
            texture_type=Texture3D,
            width=SCATTERING_TEXTURE_WIDTH,
            height=SCATTERING_TEXTURE_HEIGHT,
            depth=SCATTERING_TEXTURE_DEPTH,
            internal_format=GL_RGBA32F,
            texture_format=GL_RGBA,
            min_filter=GL_LINEAR,
            mag_filter=GL_LINEAR,
            data_type=GL_FLOAT,
            wrap=GL_CLAMP
        )

        self.delta_multiple_scattering_texture = self.delta_rayleigh_scattering_texture

        self.quad = ScreenQuad.get_vertex_array_buffer()

    def glsl_header_factory(self, lambdas):
        def to_string(v, lambdas, scale):
            r = Interpolate(self.wavelengths, v, lambdas[0]) * scale
            g = Interpolate(self.wavelengths, v, lambdas[1]) * scale
            b = Interpolate(self.wavelengths, v, lambdas[2]) * scale
            return "vec3(%f, %f, %f)" % (r, g, b)

        def density_layer(layer):
            return "DensityProfileLayer(%f, %f, %f, %f, %f)" % (layer.width / self.length_unit_in_meters,
                                                                layer.exp_term,
                                                                layer.exp_scale * self.length_unit_in_meters,
                                                                layer.linear_term * self.length_unit_in_meters,
                                                                layer.constant_term)

        def density_profile(layers):
            kLayerCount = 2
            while len(layers) < kLayerCount:
                layers.insert(0, DensityProfileLayer())

            result = "DensityProfile(DensityProfileLayer[%d](" % kLayerCount
            for i in range(kLayerCount):
                result += density_layer(layers[i])
                if i < kLayerCount - 1:
                    result += ","
                else:
                    result += "))"
            return result

        header = ["const int TRANSMITTANCE_TEXTURE_WIDTH = %d;" % TRANSMITTANCE_TEXTURE_WIDTH,
                  "const int TRANSMITTANCE_TEXTURE_HEIGHT = %d;" % TRANSMITTANCE_TEXTURE_HEIGHT,
                  "const int SCATTERING_TEXTURE_R_SIZE = %d;" % SCATTERING_TEXTURE_R_SIZE,
                  "const int SCATTERING_TEXTURE_MU_SIZE = %d;" % SCATTERING_TEXTURE_MU_SIZE,
                  "const int SCATTERING_TEXTURE_MU_S_SIZE = %d;" % SCATTERING_TEXTURE_MU_S_SIZE,
                  "const int SCATTERING_TEXTURE_NU_SIZE = %d;" % SCATTERING_TEXTURE_NU_SIZE,
                  "const int IRRADIANCE_TEXTURE_WIDTH = %d;" % IRRADIANCE_TEXTURE_WIDTH,
                  "const int IRRADIANCE_TEXTURE_HEIGHT = %d;" % IRRADIANCE_TEXTURE_HEIGHT,
                  "const vec2 IRRADIANCE_TEXTURE_SIZE = vec2(%d, %d);" % (
                    IRRADIANCE_TEXTURE_WIDTH, IRRADIANCE_TEXTURE_HEIGHT),
                  "",
                  '#include "precomputed_atmosphere/definitions.glsl"',
                  "",
                  "const AtmosphereParameters ATMOSPHERE = AtmosphereParameters(",
                  to_string(self.solar_irradiance, lambdas, 1.0) + ",",
                  str(self.sun_angular_radius) + ",",
                  str(self.bottom_radius / self.length_unit_in_meters) + ",",
                  str(self.top_radius / self.length_unit_in_meters) + ",",
                  density_profile(self.rayleigh_density) + ",",
                  to_string(self.rayleigh_scattering, lambdas, self.length_unit_in_meters) + ",",
                  density_profile(self.mie_density) + ",",
                  to_string(self.mie_scattering, lambdas, self.length_unit_in_meters) + ",",
                  to_string(self.mie_extinction, lambdas, self.length_unit_in_meters) + ",",
                  str(self.mie_phase_function_g) + ",",
                  density_profile(self.absorption_density) + ",",
                  to_string(self.absorption_extinction, lambdas, self.length_unit_in_meters) + ",",
                  to_string(self.ground_albedo, lambdas, 1.0) + ",",
                  str(cos(self.max_sun_zenith_angle)) + ");",
                  ""]
        return "\n".join(header)

    def generate(self, num_scattering_orders=4):
        resource_manager = CoreManager.instance().resource_manager
        framebuffer_manager = CoreManager.instance().renderer.framebuffer_manager

        if not self.precompute_illuminance:
            lambdas = [kLambdaR, kLambdaG, kLambdaB]
            luminance_from_radiance = Matrix3()
            self.Precompute(lambdas,
                            luminance_from_radiance,
                            False,
                            num_scattering_orders)
        else:
            num_iterations = (self.num_precomputed_wavelengths + 2) / 3
            dlambda = (kLambdaMax - kLambdaMin) / (3 * num_iterations)

            def coeff(L, component):
                x = CieColorMatchingFunctionTableValue(L, 1)
                y = CieColorMatchingFunctionTableValue(L, 2)
                z = CieColorMatchingFunctionTableValue(L, 3)
                return (XYZ_TO_SRGB[component * 3] * x +
                        XYZ_TO_SRGB[component * 3 + 1] * y +
                        XYZ_TO_SRGB[component * 3 + 2] * z) * dlambda

            for i in range(int(num_iterations)):
                lambdas = [kLambdaMin + (3 * i + 0.5) * dlambda,
                           kLambdaMin + (3 * i + 1.5) * dlambda,
                           kLambdaMin + (3 * i + 2.5) * dlambda]

                luminance_from_radiance = Matrix3()

                luminance_from_radiance[0] = [coeff(lambdas[0], 0), coeff(lambdas[1], 0), coeff(lambdas[2], 0)]
                luminance_from_radiance[1] = [coeff(lambdas[0], 1), coeff(lambdas[1], 1), coeff(lambdas[2], 1)]
                luminance_from_radiance[2] = [coeff(lambdas[0], 2), coeff(lambdas[1], 2), coeff(lambdas[2], 2)]

                self.Precompute(lambdas,
                                luminance_from_radiance,
                                0 < i,
                                num_scattering_orders)

        # Note : recompute compute_transmittance
        framebuffer_manager.bind_framebuffer(self.transmittance_texture)

        recompute_transmittance_mi = resource_manager.get_material_instance(
            'precomputed_atmosphere.recompute_transmittance',
            macros=self.material_instance_macros)
        recompute_transmittance_mi.use_program()
        self.quad.draw_elements()

        # save textures
        def save_texture(texture):
            resource = resource_manager.texture_loader.get_resource(texture.name)
            if resource is None:
                resource = resource_manager.texture_loader.create_resource(texture.name, texture)
            else:
                old_texture = resource.get_data()
                old_texture.delete()
                resource.set_data(texture)
            resource_manager.texture_loader.save_resource(resource.name)

        # precomputed textures
        save_texture(self.transmittance_texture)
        save_texture(self.scattering_texture)
        save_texture(self.irradiance_texture)

        # intermediate processing textures
        # save_texture(self.delta_irradiance_texture)
        # save_texture(self.delta_rayleigh_scattering_texture)
        # save_texture(self.delta_mie_scattering_texture)
        # save_texture(self.delta_scattering_density_texture)
        # if not self.use_combined_textures:
        #     save_texture(self.optional_single_mie_scattering_texture)

    def Precompute(self,
                   lambdas,
                   luminance_from_radiance,
                   blend,
                   num_scattering_orders):

        resource_manager = CoreManager.instance().resource_manager
        framebuffer_manager = CoreManager.instance().renderer.framebuffer_manager
        shaderLoader = resource_manager.shader_loader

        shader_name = 'precomputed_atmosphere.compute_atmosphere_predefine'
        compute_atmosphere_predefine = resource_manager.get_shader(shader_name)
        compute_atmosphere_predefine.shader_code = self.glsl_header_factory(lambdas)
        shaderLoader.save_resource(shader_name)
        shaderLoader.load_resource(shader_name)

        glEnable(GL_BLEND)
        glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(GL_ONE, GL_ONE)

        # compute_transmittance
        framebuffer_manager.bind_framebuffer(self.transmittance_texture)

        glDisablei(GL_BLEND, 0)

        compute_transmittance_mi = resource_manager.get_material_instance(
            'precomputed_atmosphere.compute_transmittance',
            macros=self.material_instance_macros)
        compute_transmittance_mi.use_program()
        self.quad.draw_elements()

        # compute_direct_irradiance
        framebuffer_manager.bind_framebuffer(self.delta_irradiance_texture, self.irradiance_texture)

        glDisablei(GL_BLEND, 0)
        if blend:
            glEnablei(GL_BLEND, 1)
        else:
            glDisablei(GL_BLEND, 1)

        compute_direct_irradiance_mi = resource_manager.get_material_instance(
            'precomputed_atmosphere.compute_direct_irradiance',
            macros=self.material_instance_macros)
        compute_direct_irradiance_mi.use_program()
        compute_direct_irradiance_mi.bind_uniform_data('transmittance_texture', self.transmittance_texture)
        self.quad.draw_elements()

        # compute_single_scattering
        compute_single_scattering_mi = resource_manager.get_material_instance(
            'precomputed_atmosphere.compute_single_scattering',
            macros=self.material_instance_macros)
        compute_single_scattering_mi.use_program()
        compute_single_scattering_mi.bind_uniform_data('luminance_from_radiance', luminance_from_radiance)
        compute_single_scattering_mi.bind_uniform_data('transmittance_texture', self.transmittance_texture)

        glDisablei(GL_BLEND, 0)
        glDisablei(GL_BLEND, 1)
        if blend:
            glEnablei(GL_BLEND, 2)
            glEnablei(GL_BLEND, 3)
        else:
            glDisablei(GL_BLEND, 2)
            glDisablei(GL_BLEND, 3)

        for layer in range(SCATTERING_TEXTURE_DEPTH):
            if self.optional_single_mie_scattering_texture is None:
                framebuffer_manager.bind_framebuffer(self.delta_rayleigh_scattering_texture,
                                                     self.delta_mie_scattering_texture,
                                                     self.scattering_texture,
                                                     target_layer=layer)
            else:
                framebuffer_manager.bind_framebuffer(self.delta_rayleigh_scattering_texture,
                                                     self.delta_mie_scattering_texture,
                                                     self.scattering_texture,
                                                     self.optional_single_mie_scattering_texture,
                                                     target_layer=layer)
            compute_single_scattering_mi.bind_uniform_data("layer", layer)
            self.quad.draw_elements()

        for scattering_order in range(2, num_scattering_orders + 1):
            # compute_scattering_density
            glDisablei(GL_BLEND, 0)

            compute_scattering_density_mi = resource_manager.get_material_instance(
                'precomputed_atmosphere.compute_scattering_density',
                macros=self.material_instance_macros
            )
            compute_scattering_density_mi.use_program()
            compute_scattering_density_mi.bind_uniform_data('transmittance_texture', self.transmittance_texture)
            compute_scattering_density_mi.bind_uniform_data('single_rayleigh_scattering_texture', self.delta_rayleigh_scattering_texture)
            compute_scattering_density_mi.bind_uniform_data('single_mie_scattering_texture', self.delta_mie_scattering_texture)
            compute_scattering_density_mi.bind_uniform_data('multiple_scattering_texture', self.delta_multiple_scattering_texture)
            compute_scattering_density_mi.bind_uniform_data('irradiance_texture', self.delta_irradiance_texture)
            compute_scattering_density_mi.bind_uniform_data('scattering_order', scattering_order)

            for layer in range(SCATTERING_TEXTURE_DEPTH):
                framebuffer_manager.bind_framebuffer(self.delta_scattering_density_texture, target_layer=layer)
                compute_scattering_density_mi.bind_uniform_data('layer', layer)
                self.quad.draw_elements()

            # compute_indirect_irradiance
            framebuffer_manager.bind_framebuffer(self.delta_irradiance_texture, self.irradiance_texture)
            glDisablei(GL_BLEND, 0)
            glEnablei(GL_BLEND, 1)

            compute_indirect_irradiance_mi = resource_manager.get_material_instance(
                'precomputed_atmosphere.compute_indirect_irradiance',
                macros=self.material_instance_macros
            )
            compute_indirect_irradiance_mi.use_program()
            compute_indirect_irradiance_mi.bind_uniform_data('luminance_from_radiance', luminance_from_radiance)
            compute_indirect_irradiance_mi.bind_uniform_data('scattering_order', scattering_order - 1)
            compute_indirect_irradiance_mi.bind_uniform_data('single_rayleigh_scattering_texture', self.delta_rayleigh_scattering_texture)
            compute_indirect_irradiance_mi.bind_uniform_data('single_mie_scattering_texture', self.delta_mie_scattering_texture)
            compute_indirect_irradiance_mi.bind_uniform_data('multiple_scattering_texture', self.delta_multiple_scattering_texture)
            self.quad.draw_elements()

            # compute_multiple_scattering
            glDisablei(GL_BLEND, 0)
            glEnablei(GL_BLEND, 1)

            compute_multiple_scattering_mi = resource_manager.get_material_instance(
                'precomputed_atmosphere.compute_multiple_scattering',
                macros=self.material_instance_macros
            )
            compute_multiple_scattering_mi.use_program()
            compute_multiple_scattering_mi.bind_uniform_data('luminance_from_radiance', luminance_from_radiance)
            compute_multiple_scattering_mi.bind_uniform_data('transmittance_texture', self.transmittance_texture)
            compute_multiple_scattering_mi.bind_uniform_data('scattering_density_texture', self.delta_scattering_density_texture)

            for layer in range(SCATTERING_TEXTURE_DEPTH):
                framebuffer_manager.bind_framebuffer(self.delta_multiple_scattering_texture, self.scattering_texture, target_layer=layer)
                compute_multiple_scattering_mi.bind_uniform_data('layer', layer)
                self.quad.draw_elements()

