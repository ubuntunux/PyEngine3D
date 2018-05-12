#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform float target_level;
uniform sampler2D texture_source;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec2 texcoord = vs_output.tex_coord.xy;
    vec2 half_texel = 0.5 / textureSize(texture_source, int(target_level));
    fs_output = texture2D(texture_source, texcoord + vec2(half_texel.x, half_texel.y), target_level);
    fs_output = min(fs_output, texture2D(texture_source, texcoord + vec2(-half_texel.x, half_texel.y), target_level));
    fs_output = min(fs_output, texture2D(texture_source, texcoord + vec2(half_texel.x, -half_texel.y), target_level));
    fs_output = min(fs_output, texture2D(texture_source, texcoord + vec2(-half_texel.x, -half_texel.y), target_level));
}
#endif // GL_FRAGMENT_SHADER