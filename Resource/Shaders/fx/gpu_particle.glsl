#include "scene_constants.glsl"
#include "utility.glsl"
#include "fx/gpu_particle_vs.glsl"


#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 ps_output;

void main()
{
    ps_output.xyz = vec3(1.0);
    ps_output.w = 1.0;
}
#endif