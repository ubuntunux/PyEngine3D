#version 430 core

#include "quad.glsl"

uniform float bloom_intensity;

uniform sampler2D texture_bloom0;
uniform sampler2D texture_bloom1;
uniform sampler2D texture_bloom2;
uniform sampler2D texture_bloom3;

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    vec2 texcoord = vs_output.texcoord.xy;

    fs_output = vec4(0.0, 0.0, 0.0, 1.0);
    fs_output.xyz += texture(texture_bloom0, texcoord).xyz * 0.9;
    fs_output.xyz += texture(texture_bloom1, texcoord).xyz * 0.7;
    fs_output.xyz += texture(texture_bloom2, texcoord).xyz * 0.5;
    fs_output.xyz += texture(texture_bloom3, texcoord).xyz * 0.3;
    fs_output.xyz *= bloom_intensity;
}
#endif // FRAGMENT_SHADER