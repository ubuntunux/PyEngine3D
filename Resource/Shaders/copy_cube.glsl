#include "scene_constants.glsl"
#include "quad.glsl"

uniform samplerCube texture_environment;
uniform mat4 face_matrix;
uniform float lod;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec3 normal;
    normal.x = vs_output.tex_coord.x * 2.0 - 1.0;
    normal.y = 1.0 - vs_output.tex_coord.y * 2.0;
    normal.z = 1.0;
    normal = normalize(normal);
    normal = (vec4(normal, 0.0) * face_matrix).xyz;
    fs_output = textureCube( texture_environment, normal, lod );
}
#endif // FRAGMENT_SHADER