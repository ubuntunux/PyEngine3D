#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_linear_depth;

#ifdef MATERIAL_COMPONENTS
    uniform vec3 fog_color;
    uniform samplerCube texture_cube;
#endif

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;

    vec4 eye_vector = (INV_VIEW_ORIGIN * INV_PROJECTION * vec4(vs_output.position, 1.0));
    eye_vector.xyz /= eye_vector.w;
    eye_vector.xyz = normalize(eye_vector.xyz);

    float linear_depth = texture(texture_linear_depth, tex_coord).x;
    float opacity = pow(clamp(linear_depth * 0.01, 0.0, 1.0), 2.0);

    // Note : use inverted Y-Axis
    vec3 environment = texture(texture_cube, invert_y(eye_vector.xyz)).xyz;
    environment = pow(environment, vec3(2.2));

    fs_output.xyz = (NEAR_FAR.y - 0.001) <= linear_depth ? environment : fog_color;

    // Sun
    fs_output.xyz += LIGHT_COLOR.xyz * vec3(pow(clamp(dot(eye_vector.xyz, LIGHT_DIRECTION.xyz) * 100.0 - 99.0, 0.0, 1.0), 100.0));

    fs_output.w = opacity;
}
#endif