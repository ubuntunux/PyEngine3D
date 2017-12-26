from math import cos, sin
import numpy as np

from .constants import *
from .shaders import *

from Utilities import *


def CieColorMatchingFunctionTableValue(wavelength, column):
    if wavelength <= kLambdaMin or wavelength >= kLambdaMax:
        return 0.0

    u = (wavelength - kLambdaMin) / 5.0
    row = int(u)
    assert(row >= 0 and row + 1 < 95)
    assert(CIE_2_DEG_COLOR_MATCHING_FUNCTIONS[4 * row] <= wavelength and
           CIE_2_DEG_COLOR_MATCHING_FUNCTIONS[4 * (row + 1)] >= wavelength)

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
                 combine_scattering_textures,
                 half_precision,
                 definitions_glsl,
                 functions_glsl):

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
        self.combine_scattering_textures = combine_scattering_textures
        self.half_precision = half_precision
        self.definitions_glsl = definitions_glsl
        self.functions_glsl = functions_glsl

        precompute_illuminance = num_precomputed_wavelengths > 3
        if precompute_illuminance:
            self.kSky = [MAX_LUMINOUS_EFFICACY, MAX_LUMINOUS_EFFICACY, MAX_LUMINOUS_EFFICACY]
        else:
            self.kSky = ComputeSpectralRadianceToLuminanceFactors(self.wavelengths, self.solar_irradiance, -3)
        self.kSun = ComputeSpectralRadianceToLuminanceFactors(self.wavelengths, self.solar_irradiance, 0)

        self.atmosphere_shader_source = self.glsl_header_factory([kLambdaR, kLambdaG, kLambdaB])
        if not precompute_illuminance:
            self.atmosphere_shader_source += "#define RADIANCE_API_ENABLED\n"
        self.atmosphere_shader_source += kAtmosphereShader

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

        sky_k_r, sky_k_g, sky_k_b = self.kSky[0], self.kSky[1], self.kSky[2]
        sun_k_r, sun_k_g, sun_k_b = self.kSun[0], self.kSun[1], self.kSun[2]

        header = ["#define IN(x) const in x",
                  "#define OUT(x) out x",
                  "#define TEMPLATE(x)",
                  "#define TEMPLATE_ARGUMENT(x)",
                  "#define assert(x)",
                  "const int TRANSMITTANCE_TEXTURE_WIDTH = %d;" % TRANSMITTANCE_TEXTURE_WIDTH,
                  "const int TRANSMITTANCE_TEXTURE_HEIGHT = %d;" % TRANSMITTANCE_TEXTURE_HEIGHT,
                  "const int SCATTERING_TEXTURE_R_SIZE = %d;" % SCATTERING_TEXTURE_R_SIZE,
                  "const int SCATTERING_TEXTURE_MU_SIZE = %d;" % SCATTERING_TEXTURE_MU_SIZE,
                  "const int SCATTERING_TEXTURE_MU_S_SIZE = %d;" % SCATTERING_TEXTURE_MU_S_SIZE,
                  "const int SCATTERING_TEXTURE_NU_SIZE = %d;" % SCATTERING_TEXTURE_NU_SIZE,
                  "const int IRRADIANCE_TEXTURE_WIDTH = %d;" % IRRADIANCE_TEXTURE_WIDTH,
                  "const int IRRADIANCE_TEXTURE_HEIGHT = %d;" % IRRADIANCE_TEXTURE_HEIGHT,
                  "#define COMBINED_SCATTERING_TEXTURES" if self.combine_scattering_textures else "",
                  self.definitions_glsl,
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
                  "const vec3 SKY_SPECTRAL_RADIANCE_TO_LUMINANCE = vec3(%f, %f, %f);" % (sky_k_r, sky_k_g, sky_k_b),
                  "const vec3 SUN_SPECTRAL_RADIANCE_TO_LUMINANCE = vec3(%f, %f, %f);" % (sun_k_r, sun_k_g, sun_k_b),
                  self.functions_glsl]
        return "\n".join(header)

    def Init(self, num_scattering_orders = 4):
        if self.num_precomputed_wavelengths <= 3:
            lambdas = [kLambdaR, kLambdaG, kLambdaB]
            luminance_from_radiance = Matrix3()
            Precompute(fbo,
                       delta_irradiance_texture,
                       delta_rayleigh_scattering_texture,
                       delta_mie_scattering_texture,
                       delta_scattering_density_texture,
                       delta_multiple_scattering_texture,
                       lambdas,
                       luminance_from_radiance,
                       false,
                       num_scattering_orders)
        else:
            num_iterations = (num_precomputed_wavelengths_ + 2) / 3
            dlambda = (kLambdaMax - kLambdaMin) / (3 * num_iterations)

            def coeff(L, component):
                x = CieColorMatchingFunctionTableValue(L, 1)
                y = CieColorMatchingFunctionTableValue(L, 2)
                z = CieColorMatchingFunctionTableValue(L, 3)
                return (XYZ_TO_SRGB[component * 3] * x +
                        XYZ_TO_SRGB[component * 3 + 1] * y +
                        XYZ_TO_SRGB[component * 3 + 2] * z) * dlambda

            for i in range(num_iterations):
                lambdas = [kLambdaMin + (3 * i + 0.5) * dlambda,
                           kLambdaMin + (3 * i + 1.5) * dlambda,
                           kLambdaMin + (3 * i + 2.5) * dlambda]

                luminance_from_radiance = Matrix3()

                luminance_from_radiance[0] = [coeff(lambdas[0], 0), coeff(lambdas[1], 0), coeff(lambdas[2], 0)]
                luminance_from_radiance[1] = [coeff(lambdas[0], 1), coeff(lambdas[1], 1), coeff(lambdas[2], 1)]
                luminance_from_radiance[2] = [coeff(lambdas[0], 2), coeff(lambdas[1], 2), coeff(lambdas[2], 2)]

                Precompute(fbo,
                    delta_irradiance_texture,
                    delta_rayleigh_scattering_texture,
                    delta_mie_scattering_texture,
                    delta_scattering_density_texture,
                    delta_multiple_scattering_texture,
                    lambdas,
                    luminance_from_radiance, i > 0,
                    num_scattering_orders)
        header = glsl_header_factory_([kLambdaR, kLambdaG, kLambdaB])
        self.vertex_shader_code = kVertexShader
        self.fragment_shader_code = header + kComputeTransmittanceShader


    def GetShader():
        return atmosphere_shader

    def SetProgramUniforms(
          program,
          transmittance_texture_unit,
          scattering_texture_unit,
          irradiance_texture_unit,
          optional_single_mie_scattering_texture_unit=0):
        pass

    def Precompute(
            fbo,
            delta_irradiance_texture,
            delta_rayleigh_scattering_texture,
            delta_mie_scattering_texture,
            delta_scattering_density_texture,
            delta_multiple_scattering_texture,
            lambdas,
            luminance_from_radiance,
            blend,
            num_scattering_orders):
        pass