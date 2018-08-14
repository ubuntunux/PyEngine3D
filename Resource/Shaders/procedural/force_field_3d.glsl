#include "scene_constants.glsl"
#include "quad.glsl"

uniform float depth;


#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    // vec3 uvw = vec3(vs_output.tex_coord, depth);
    fs_output.xz = vec2(-vs_output.tex_coord.y, vs_output.tex_coord.x);
    fs_output.y = 0.0;
    fs_output.w = 1.0;
}
#endif