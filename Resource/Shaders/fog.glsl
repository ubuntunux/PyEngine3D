#version 430 core

#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_depth;

#ifdef MATERIAL_COMPONENTS
    uniform vec3 fog_color = vec3(1.0, 1.0, 1.0);
#endif


#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    vec2 texcoord = vs_output.texcoord.xy;

    float depth = texture(texture_depth, texcoord).x;
    float linear_depth = depth_to_distance(near_far.x, near_far.y, depth);
    fs_output.xyz = fog_color;
    fs_output.a = linear_depth < near_far.y ? pow(clamp(linear_depth * 0.01, 0.0, 1.0), 2.0) : 0.0;
}
#endif // FRAGMENT_SHADER