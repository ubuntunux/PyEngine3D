#include "ocean_vs.glsl"


#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 uv = vs_output.tex_coord.xy;
    float noise = texture(texture_noise, uv).x;

    fs_output.xyz = vec3(noise);
    fs_output.a = 1.0;
}
#endif // GL_FRAGMENT_SHADER
