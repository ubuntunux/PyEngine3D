#include "ocean_vs.glsl"

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 uv = vs_output.tex_coord.xy;
    vec3 foam = texture(texture_foam, uv * uv_tiling).xyz;

    fs_output.xyz = foam;//* clamp(vs_output.wave_offset.y, 0.2, 1.0);

    fs_output.a = 1.0;
}
#endif // GL_FRAGMENT_SHADER
