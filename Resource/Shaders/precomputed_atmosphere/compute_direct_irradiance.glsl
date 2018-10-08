#include "precomputed_atmosphere/compute_atmosphere_predefine.glsl"
#include "precomputed_atmosphere/precompute_vs.glsl"

#ifdef FRAGMENT_SHADER
layout(location = 0) out vec3 delta_irradiance;
layout(location = 1) out vec3 irradiance;

void main()
{
    delta_irradiance = ComputeDirectIrradiancetexture2D(ATMOSPHERE, transmittance_texture, gl_FragCoord.xy);
    irradiance = vec3(0.0);
}
#endif