#include "scene_constants.glsl"
#include "quad.glsl"



#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

uniform float depth;
uniform float noise_persistance;
uniform int noise_scale;

void main() {
    vec3 st = vec3(vs_output.tex_coord, depth);
    float n = perlinNoise( st, float(noise_scale), noise_persistance);
    fs_output = vec4(n);
}
#endif