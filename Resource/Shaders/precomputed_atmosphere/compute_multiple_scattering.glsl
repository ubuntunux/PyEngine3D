#include "precomputed_atmosphere/compute_atmosphere_predefine.glsl"
#include "precomputed_atmosphere/precompute_vs.glsl"

#ifdef FRAGMENT_SHADER
layout(location = 0) out vec3 delta_multiple_scattering;
layout(location = 1) out vec4 scattering;

uniform mat3 luminance_from_radiance;
uniform int layer;

void main()
{
    float nu;
    delta_multiple_scattering = ComputeMultipleScatteringtexture2D(
        ATMOSPHERE, transmittance_texture, scattering_density_texture,
        vec3(gl_FragCoord.xy, layer + 0.5), nu);
    scattering = vec4(luminance_from_radiance * delta_multiple_scattering.rgb / RayleighPhaseFunction(nu), 0.0);
}
#endif