#include "quad.glsl"

uniform samplerCube texture_environment;
uniform mat4 face_matrix;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec3 tex_coord;
     tex_coord.x = vs_output.tex_coord.x * 2.0 - 1.0;
     tex_coord.y = 1.0 - vs_output.tex_coord.y * 2.0;
     tex_coord.z = 1.0;
     tex_coord = normalize(tex_coord);
     tex_coord = (vec4(tex_coord, 0.0) * face_matrix).xyz;

    fs_output = texture(texture_environment, tex_coord);
}
#endif // GL_FRAGMENT_SHADER