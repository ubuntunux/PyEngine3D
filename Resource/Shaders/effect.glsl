#include "scene_constants.glsl"
#include "utility.glsl"
#include "effect_vs.glsl"

uniform sampler2D texture_diffuse;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 color;

void main()
{
    color = texture2D(texture_linear_depth, tex_coord, texture_lod).x;
    vec4(1, 0, 1, vs_output.opacity);
}
#endif