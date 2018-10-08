#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "default_vs.glsl"


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;

layout (location = 0) out vec4 fs_ouptut;

void main()
{
    fs_ouptut = vec4(1.0, 1.0, 1.0, 1.0);
}
#endif