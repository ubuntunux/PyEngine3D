#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_atmosphere;
uniform sampler2D texture_depth;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec2 texcoord = vs_output.tex_coord.xy;
    float depth = texture2D(texture_depth, texcoord).x;
    fs_output = texture2D(texture_atmosphere, texcoord);
    fs_output.a = depth == 1.0 ? 1.0 : 0.0;
}
#endif // GL_FRAGMENT_SHADER