#version 430 core

#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

#ifdef MATERIAL_COMPONENTS
    uniform samplerCube texture_cube;
#endif

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;

out vec4 fs_output;

void main() {
    vec3 eye_vector = (inv_view_origin * inv_perspective * vec4(vs_output.position, 1.0)).xyz;
    eye_vector = normalize(eye_vector);

    // Note : use inverted Y-Axis
    fs_output.xyz = texture(texture_cube, invert_y(eye_vector.xyz)).xyz;
    fs_output.xyz = pow(fs_output.xyz, vec3(2.2));

    // Sun
    fs_output.xyz += lightColor.xyz * vec3(pow(clamp(dot(eye_vector, lightDir.xyz) * 100.0 - 99.0, 0.0, 1.0), 100.0));
    fs_output.a = 1.0;
}
#endif // FRAGMENT_SHADER