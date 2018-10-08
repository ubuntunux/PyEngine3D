#include "scene_constants.glsl"
#include "quad.glsl"

uniform float depth;


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec3 uvw = vec3(vs_output.tex_coord, depth);
    fs_output.xyz = -(uvw * 2.0 - 1.0);
    fs_output.xyz -= (uvw + 0.2) * 2.0 - 1.0;
    fs_output.xyz -= (uvw + vec3(0.5, -0.8, 0.3)) * 2.0 - 1.0;
    fs_output.xyz -= (uvw + vec3(0.9, -0.2, -0.3)) * 2.0 - 1.0;
    fs_output.xyz -= (uvw + vec3(-0.2, 0.3, 0.7)) * 2.0 - 1.0;
    fs_output.w = 1.0;
}
#endif