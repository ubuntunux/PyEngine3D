

#include "utility.glsl"
#include "quad.glsl"

uniform sampler2D texture_depth;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    float depth = texture2D(texture_depth, vs_output.tex_coord.xy).x;
    fs_output = vec4(depth_to_linear_depth(depth));
}
#endif // FRAGMENT_SHADER