#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_linear_depth;

#ifdef MATERIAL_COMPONENTS
    uniform vec3 fog_color;
    uniform samplerCube texture_cube;
#endif

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;

    vec4 eye_vector = (INV_VIEW_ORIGIN * INV_PROJECTION * vec4(vs_output.position, 1.0));
    eye_vector.xyz /= eye_vector.w;
    eye_vector.xyz = normalize(eye_vector.xyz);

    // Note : use inverted Y-Axis
    fs_output.xyz = texture(texture_cube, invert_y(eye_vector.xyz)).xyz;
    fs_output.xyz = pow(fs_output.xyz, vec3(2.2));

    // Sun
    fs_output.xyz += LIGHT_COLOR.xyz * vec3(pow(clamp(dot(eye_vector.xyz, LIGHT_DIRECTION.xyz) * 100.0 - 99.0, 0.0, 1.0), 100.0));

    // fog
    float linear_depth = texture(texture_linear_depth, tex_coord).x;
    fs_output.xyz = mix(fs_output.xyz, fog_color, linear_depth < NEAR_FAR.y ? 1.0 : 0.0);
    fs_output.w = linear_depth < NEAR_FAR.y ? pow(clamp(linear_depth * 0.01, 0.0, 1.0), 2.0) : clamp(linear_depth, 0.0, 1.0);
}
#endif