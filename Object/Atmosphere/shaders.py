kDemoVertexShader = """
    #version 330
    uniform mat4 model_from_view;
    uniform mat4 view_from_clip;
    layout(location = 0) in vec4 vertex;
    out vec3 view_ray;
    void main() {
      view_ray = (model_from_view * vec4((view_from_clip * vertex).xyz, 0.0)).xyz;
      gl_Position = vertex;
    }"""

kVertexShader = """
    #version 330
    layout(location = 0) in vec2 vertex;
    void main() {
      gl_Position = vec4(vertex, 0.0, 1.0);
    }"""

kGeometryShader = """
    #version 330
    layout(triangles) in;
    layout(triangle_strip, max_vertices = 3) out;
    uniform int layer;
    void main() {
      gl_Position = gl_in[0].gl_Position;
      gl_Layer = layer;
      EmitVertex();
      gl_Position = gl_in[1].gl_Position;
      gl_Layer = layer;
      EmitVertex();
      gl_Position = gl_in[2].gl_Position;
      gl_Layer = layer;
      EmitVertex();
      EndPrimitive();
    }"""

kComputeTransmittanceShader = """
    layout(location = 0) out vec3 transmittance;
    void main() {
      transmittance = ComputeTransmittanceToTopAtmosphereBoundaryTexture(
          ATMOSPHERE, gl_FragCoord.xy);
    }"""

kComputeDirectIrradianceShader = """
    layout(location = 0) out vec3 delta_irradiance;
    layout(location = 1) out vec3 irradiance;
    uniform sampler2D transmittance_texture;
    void main() {
      delta_irradiance = ComputeDirectIrradianceTexture(
          ATMOSPHERE, transmittance_texture, gl_FragCoord.xy);
      irradiance = vec3(0.0);
    }"""

kComputeSingleScatteringShader = """
    layout(location = 0) out vec3 delta_rayleigh;
    layout(location = 1) out vec3 delta_mie;
    layout(location = 2) out vec4 scattering;
    layout(location = 3) out vec3 single_mie_scattering;
    uniform mat3 luminance_from_radiance;
    uniform sampler2D transmittance_texture;
    uniform int layer;
    void main() {
      ComputeSingleScatteringTexture(
          ATMOSPHERE, transmittance_texture, vec3(gl_FragCoord.xy, layer + 0.5),
          delta_rayleigh, delta_mie);
      scattering = vec4(luminance_from_radiance * delta_rayleigh.rgb,
          (luminance_from_radiance * delta_mie).r);
      single_mie_scattering = luminance_from_radiance * delta_mie;
    }"""

kComputeScatteringDensityShader = """
    layout(location = 0) out vec3 scattering_density;
    uniform sampler2D transmittance_texture;
    uniform sampler3D single_rayleigh_scattering_texture;
    uniform sampler3D single_mie_scattering_texture;
    uniform sampler3D multiple_scattering_texture;
    uniform sampler2D irradiance_texture;
    uniform int scattering_order;
    uniform int layer;
    void main() {
      scattering_density = ComputeScatteringDensityTexture(
          ATMOSPHERE, transmittance_texture, single_rayleigh_scattering_texture,
          single_mie_scattering_texture, multiple_scattering_texture,
          irradiance_texture, vec3(gl_FragCoord.xy, layer + 0.5),
          scattering_order);
    }"""

kComputeIndirectIrradianceShader = """
    layout(location = 0) out vec3 delta_irradiance;
    layout(location = 1) out vec3 irradiance;
    uniform mat3 luminance_from_radiance;
    uniform sampler3D single_rayleigh_scattering_texture;
    uniform sampler3D single_mie_scattering_texture;
    uniform sampler3D multiple_scattering_texture;
    uniform int scattering_order;
    void main() {
      delta_irradiance = ComputeIndirectIrradianceTexture(
          ATMOSPHERE, single_rayleigh_scattering_texture,
          single_mie_scattering_texture, multiple_scattering_texture,
          gl_FragCoord.xy, scattering_order);
      irradiance = luminance_from_radiance * delta_irradiance;
    }"""

kComputeMultipleScatteringShader = """
    layout(location = 0) out vec3 delta_multiple_scattering;
    layout(location = 1) out vec4 scattering;
    uniform mat3 luminance_from_radiance;
    uniform sampler2D transmittance_texture;
    uniform sampler3D scattering_density_texture;
    uniform int layer;
    void main() {
      float nu;
      delta_multiple_scattering = ComputeMultipleScatteringTexture(
          ATMOSPHERE, transmittance_texture, scattering_density_texture,
          vec3(gl_FragCoord.xy, layer + 0.5), nu);
      scattering = vec4(
          luminance_from_radiance *
              delta_multiple_scattering.rgb / RayleighPhaseFunction(nu),
          0.0);
    }"""

kAtmosphereShader = """
    uniform sampler2D transmittance_texture;
    uniform sampler3D scattering_texture;
    uniform sampler3D single_mie_scattering_texture;
    uniform sampler2D irradiance_texture;
    #ifdef RADIANCE_API_ENABLED
    RadianceSpectrum GetSolarRadiance() {
      return ATMOSPHERE.solar_irradiance /
          (PI * ATMOSPHERE.sun_angular_radius * ATMOSPHERE.sun_angular_radius);
    }
    RadianceSpectrum GetSkyRadiance(
        Position camera, Direction view_ray, Length shadow_length,
        Direction sun_direction, out DimensionlessSpectrum transmittance) {
      return GetSkyRadiance(ATMOSPHERE, transmittance_texture,
          scattering_texture, single_mie_scattering_texture,
          camera, view_ray, shadow_length, sun_direction, transmittance);
    }
    RadianceSpectrum GetSkyRadianceToPoint(
        Position camera, Position point, Length shadow_length,
        Direction sun_direction, out DimensionlessSpectrum transmittance) {
      return GetSkyRadianceToPoint(ATMOSPHERE, transmittance_texture,
          scattering_texture, single_mie_scattering_texture,
          camera, point, shadow_length, sun_direction, transmittance);
    }
    IrradianceSpectrum GetSunAndSkyIrradiance(
       Position p, Direction normal, Direction sun_direction,
       out IrradianceSpectrum sky_irradiance) {
      return GetSunAndSkyIrradiance(ATMOSPHERE, transmittance_texture,
          irradiance_texture, p, normal, sun_direction, sky_irradiance);
    }
    #endif
    Luminance3 GetSolarLuminance() {
      return ATMOSPHERE.solar_irradiance /
          (PI * ATMOSPHERE.sun_angular_radius * ATMOSPHERE.sun_angular_radius) *
          SUN_SPECTRAL_RADIANCE_TO_LUMINANCE;
    }
    Luminance3 GetSkyLuminance(
        Position camera, Direction view_ray, Length shadow_length,
        Direction sun_direction, out DimensionlessSpectrum transmittance) {
      return GetSkyRadiance(ATMOSPHERE, transmittance_texture,
          scattering_texture, single_mie_scattering_texture,
          camera, view_ray, shadow_length, sun_direction, transmittance) *
          SKY_SPECTRAL_RADIANCE_TO_LUMINANCE;
    }
    Luminance3 GetSkyLuminanceToPoint(
        Position camera, Position point, Length shadow_length,
        Direction sun_direction, out DimensionlessSpectrum transmittance) {
      return GetSkyRadianceToPoint(ATMOSPHERE, transmittance_texture,
          scattering_texture, single_mie_scattering_texture,
          camera, point, shadow_length, sun_direction, transmittance) *
          SKY_SPECTRAL_RADIANCE_TO_LUMINANCE;
    }
    Illuminance3 GetSunAndSkyIlluminance(
       Position p, Direction normal, Direction sun_direction,
       out IrradianceSpectrum sky_irradiance) {
      IrradianceSpectrum sun_irradiance = GetSunAndSkyIrradiance(
          ATMOSPHERE, transmittance_texture, irradiance_texture, p, normal,
          sun_direction, sky_irradiance);
      sky_irradiance *= SKY_SPECTRAL_RADIANCE_TO_LUMINANCE;
      return sun_irradiance * SUN_SPECTRAL_RADIANCE_TO_LUMINANCE;
    }"""


definitions_glsl = """
#define Length float
#define Wavelength float
#define Angle float
#define SolidAngle float
#define Power float
#define LuminousPower float

#define Number float
#define InverseLength float
#define Area float
#define Volume float
#define NumberDensity float
#define Irradiance float
#define Radiance float
#define SpectralPower float
#define SpectralIrradiance float
#define SpectralRadiance float
#define SpectralRadianceDensity float
#define ScatteringCoefficient float
#define InverseSolidAngle float
#define LuminousIntensity float
#define Luminance float
#define Illuminance float

#define AbstractSpectrum vec3
#define DimensionlessSpectrum vec3
#define PowerSpectrum vec3
#define IrradianceSpectrum vec3
#define RadianceSpectrum vec3
#define RadianceDensitySpectrum vec3
#define ScatteringSpectrum vec3

#define Position vec3
#define Direction vec3
#define Luminance3 vec3
#define Illuminance3 vec3

#define TransmittanceTexture sampler2D
#define AbstractScatteringTexture sampler3D
#define ReducedScatteringTexture sampler3D
#define ScatteringTexture sampler3D
#define ScatteringDensityTexture sampler3D
#define IrradianceTexture sampler2D

const Length m = 1.0;
const Wavelength nm = 1.0;
const Angle rad = 1.0;
const SolidAngle sr = 1.0;
const Power watt = 1.0;
const LuminousPower lm = 1.0;
const float PI = 3.14159265358979323846;
const Length km = 1000.0 * m;
const Area m2 = m * m;
const Volume m3 = m * m * m;
const Angle pi = PI * rad;
const Angle deg = pi / 180.0;
const Irradiance watt_per_square_meter = watt / m2;
const Radiance watt_per_square_meter_per_sr = watt / (m2 * sr);
const SpectralIrradiance watt_per_square_meter_per_nm = watt / (m2 * nm);
const SpectralRadiance watt_per_square_meter_per_sr_per_nm = watt / (m2 * sr * nm);
const SpectralRadianceDensity watt_per_cubic_meter_per_sr_per_nm = watt / (m3 * sr * nm);
const LuminousIntensity cd = lm / sr;
const LuminousIntensity kcd = 1000.0 * cd;
const Luminance cd_per_square_meter = cd / m2;
const Luminance kcd_per_square_meter = kcd / m2;


struct DensityProfileLayer {
  Length width;
  Number exp_term;
  InverseLength exp_scale;
  InverseLength linear_term;
  Number constant_term;
};

struct DensityProfile {
  DensityProfileLayer layers[2];
};

struct AtmosphereParameters {
  IrradianceSpectrum solar_irradiance;
  Angle sun_angular_radius;
  Length bottom_radius;
  Length top_radius;
  DensityProfile rayleigh_density;
  ScatteringSpectrum rayleigh_scattering;
  DensityProfile mie_density;
  ScatteringSpectrum mie_scattering;
  ScatteringSpectrum mie_extinction;
  Number mie_phase_function_g;
  DensityProfile absorption_density;
  ScatteringSpectrum absorption_extinction;
  DimensionlessSpectrum ground_albedo;
  Number mu_s_min;
};
"""