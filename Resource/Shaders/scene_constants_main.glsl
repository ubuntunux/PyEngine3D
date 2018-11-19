#include "scene_constants.glsl"
#include "quad.glsl"


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    fs_output = vec4(1.0, 0.0, 0.0, 1.0);
}
#endif