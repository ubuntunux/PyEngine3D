#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform float texture_lod;
uniform samplerCube texture_source;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec4 position = vec4(vs_output.tex_coord.xy * 2.0 - 1.0 + JITTER_OFFSET, -1.0, 1.0);
    position = INV_VIEW_ORIGIN * INV_PROJECTION * position;
    position.xyz /= position.w;
    position.y = -position.y;
    fs_output = texture(texture_source, normalize(position.xyz), texture_lod);
}
#endif // GL_FRAGMENT_SHADER