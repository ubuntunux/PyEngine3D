#version 430 core

#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

#ifdef MATERIAL_COMPONENTS
    uniform samplerCube texture_cube;
#endif

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec4 eye_vector = (INV_VIEW_ORIGIN * INV_PERSPECTIVE * vec4(vs_output.position, 1.0));
    eye_vector.xyz /= eye_vector.w;
    eye_vector.xyz = normalize(eye_vector.xyz);

    // Note : use inverted Y-Axis
    fs_output.xyz = texture(texture_cube, invert_y(eye_vector.xyz)).xyz;
    fs_output.xyz = pow(fs_output.xyz, vec3(2.2));

    // Sun
    fs_output.xyz += LIGHT_COLOR.xyz * vec3(pow(clamp(dot(eye_vector.xyz, LIGHT_DIRECTION.xyz) * 100.0 - 99.0, 0.0, 1.0), 100.0));
    fs_output.a = 1.0;
}
#endif // FRAGMENT_SHADER