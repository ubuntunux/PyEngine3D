#include "quad.glsl"

uniform sampler2D texture_luminance;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;
    int lod = max(0, textureQueryLevels(texture_luminance) - 1);

    vec2 texel_size = 1.0 / textureSize(texture_luminance, lod);

    fs_output.xyz = texture(texture_luminance, vec2(0.5, 0.5), float(lod)).xxx;
    fs_output.xyz = clamp(fs_output.xyz, vec3(0.2), vec3(10.0));
    fs_output.w = 0.05;
}
#endif // GL_FRAGMENT_SHADER