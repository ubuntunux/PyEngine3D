

#include "utility.glsl"
#include "quad.glsl"

uniform float bloom_threshold_min;
uniform float bloom_threshold_max;

uniform sampler2D texture_diffuse;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;
    vec3 result = vec3(0.0, 0.0, 0.0);
    result = texture(texture_diffuse, tex_coord).xyz;
    float luminance = get_luminance(result);
    result = vec3(smoothstep(bloom_threshold_min, bloom_threshold_max, luminance));
    fs_output = vec4(result, 1.0);
}
#endif // GL_FRAGMENT_SHADER