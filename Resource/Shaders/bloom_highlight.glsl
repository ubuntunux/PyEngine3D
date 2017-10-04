#version 430 core

#include "utility.glsl"
#include "quad.glsl"

uniform float bloom_threshold;

uniform sampler2D texture_diffuse;

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    vec2 texcoord = vs_output.texcoord.xy;
    vec3 result = vec3(0.0, 0.0, 0.0);
    result = texture(texture_diffuse, texcoord).xyz;
    float luminance = get_luminance(result);
    result = vec3(smoothstep(bloom_threshold, 1.5, luminance));
    fs_output = vec4(result, 1.0);
}
#endif // FRAGMENT_SHADER