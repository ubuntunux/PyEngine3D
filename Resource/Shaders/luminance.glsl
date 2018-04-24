#include "utility.glsl"
#include "quad.glsl"

uniform sampler2D texture_source;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out float fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;
    fs_output = get_luminance(texture(texture_source, tex_coord).xyz);
}
#endif // GL_FRAGMENT_SHADER