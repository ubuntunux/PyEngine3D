#include "precomputed_scattering/atmosphere_predefine.glsl"
#include "precomputed_scattering/precompute_vs.glsl"

#ifdef GL_FRAGMENT_SHADER
layout(location = 0) out vec3 transmittance;
void main() {
  transmittance = ComputeTransmittanceToTopAtmosphereBoundaryTexture(
      ATMOSPHERE, gl_FragCoord.xy);
}
#endif