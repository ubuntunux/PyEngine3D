#include "precomputed_atmosphere/compute_atmosphere_predefine.glsl"
#include "precomputed_atmosphere/precompute_vs.glsl"

#ifdef FRAGMENT_SHADER
layout(location = 0) out vec3 scattering_density;

uniform int scattering_order;
uniform int layer;

void main()
{
    scattering_density = ComputeScatteringDensitytexture2D(
        ATMOSPHERE, transmittance_texture, single_rayleigh_scattering_texture,
        single_mie_scattering_texture, multiple_scattering_texture,
        irradiance_texture, vec3(gl_FragCoord.xy, layer + 0.5),
        scattering_order);
}
#endif