#include "scene_constants.glsl"
#include "utility.glsl"
#include "effect_vs.glsl"


uniform sampler2D texture_diffuse;
uniform vec3 color;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 ps_output;

void main()
{
    vec4 diffuse = texture2D(texture_diffuse, vs_output.tex_coord);
    ps_output.xyz = pow(diffuse.xyz, vec3(2.2)) * color.xyz;
    ps_output.w = diffuse.w * vs_output.opacity;
}
#endif