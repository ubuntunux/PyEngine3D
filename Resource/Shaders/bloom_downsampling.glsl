#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_source;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 texcoord = vs_output.tex_coord.xy;

    vec2 inv_texture_size = 1.0 / textureSize(texture_source, 0);
    fs_output = texture2D(texture_source, texcoord);

    vec4 color = texture2D(texture_source, texcoord + vec2(inv_texture_size.x, 0.0));
    float luminance = get_luminance(color.xyz);
    fs_output = mix(fs_output, color, clamp(luminance, 0.0, 1.0));

    color = texture2D(texture_source, texcoord + vec2(0.0, inv_texture_size.y));
    luminance = get_luminance(color.xyz);
    fs_output = mix(fs_output, color, clamp(luminance, 0.0, 1.0));

    color = texture2D(texture_source, texcoord + inv_texture_size);
    luminance = get_luminance(color.xyz);
    fs_output = mix(fs_output, color, clamp(luminance, 0.0, 1.0));
}
#endif // FRAGMENT_SHADER