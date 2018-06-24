#include "scene_constants.glsl"
#include "utility.glsl"
#include "effect_vs.glsl"


#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 color;

void main()
{
    color = vec4(1, 0, 1, 1);
}
#endif