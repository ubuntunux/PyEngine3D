#version 430 core

#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform bool is_depth_texture;
uniform sampler2D texture_diffuse;

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    fs_output = texture(texture_diffuse, vs_output.texcoord.xy);
    if(is_depth_texture)
    {
        float distance = distance_to_depth(near_far.x, near_far.y, fs_output.x);
        fs_output.xyz = vec3(distance);
    }
    fs_output.a = 1.0;
}
#endif // FRAGMENT_SHADER