#include "precomputed_atmosphere/compute_atmosphere_predefine.glsl"
#include "precomputed_atmosphere/precompute_vs.glsl"

#ifdef FRAGMENT_SHADER

layout(location = 0) out vec3 transmittance;

void main()
{
    transmittance = ComputeTransmittanceToTopAtmosphereBoundarytexture2D(ATMOSPHERE, gl_FragCoord.xy);
}
#endif