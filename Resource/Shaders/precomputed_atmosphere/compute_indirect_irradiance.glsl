#include "precomputed_atmosphere/compute_atmosphere_predefine.glsl"
#include "precomputed_atmosphere/precompute_vs.glsl"

#ifdef FRAGMENT_SHADER
layout(location = 0) out vec3 delta_irradiance;
layout(location = 1) out vec3 irradiance;

uniform mat3 luminance_from_radiance;
uniform int scattering_order;

void main()
{
    delta_irradiance = ComputeIndirectIrradiancetexture2D(
        ATMOSPHERE, single_rayleigh_scattering_texture,
        single_mie_scattering_texture, multiple_scattering_texture,
        gl_FragCoord.xy, scattering_order);

    irradiance = luminance_from_radiance * delta_irradiance;
}
#endif