#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_lightshaft;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec2 texcoord = vs_output.tex_coord.xy;
    fs_output = texture2D(texture_lightshaft, texcoord);
}
#endif // GL_FRAGMENT_SHADER