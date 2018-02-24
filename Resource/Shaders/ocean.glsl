#include "ocean_vs.glsl"

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 uv = vs_output.tex_coord.xy;
    vec3 foam = texture(texture_foam, uv * uv_tiling).xyz;

    float diffuse_lighting = clamp(dot(LIGHT_DIRECTION.xyz, normalize(vs_output.wave_normal)), 0.0, 1.0);

    fs_output.xyz = foam * diffuse_lighting;
    fs_output.a = 1.0;
}
#endif // GL_FRAGMENT_SHADER
