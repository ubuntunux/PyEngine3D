#include "quad.glsl"

uniform sampler2D texture_static_shadowmap;
uniform sampler2D texture_dynamic_shadowmap;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;

    fs_output = vec4(min(texture2D(texture_static_shadowmap, tex_coord).x, texture2D(texture_dynamic_shadowmap, tex_coord).x));
}
#endif // FRAGMENT_SHADER