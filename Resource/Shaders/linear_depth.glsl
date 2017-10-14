#version 430 core

#include "utility.glsl"
#include "quad.glsl"

uniform sampler2D texture_depth;

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    float depth = texture(texture_depth, vs_output.texcoord.xy).x;
    fs_output = vec4(depth_to_linear_depth(depth));
}
#endif // FRAGMENT_SHADER