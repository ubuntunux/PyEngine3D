

#include "utility.glsl"
#include "quad.glsl"

uniform float bloom_threshold_min;
uniform float bloom_threshold_max;

uniform sampler2D texture_diffuse;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;
    vec3 color = max(vec3(0.0), texture2D(texture_diffuse, tex_coord).xyz);
    float luminance = max(0.01, get_luminance(color));
    color = color * min(bloom_threshold_max, max(0.0, luminance - bloom_threshold_min)) / luminance;
    fs_output = vec4(color, 1.0);
}
#endif // FRAGMENT_SHADER