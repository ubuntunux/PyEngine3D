#version 430 core

#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform bool is_depth_texture;
uniform sampler2D texture_source;

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    fs_output = texture(texture_source, vs_output.tex_coord.xy);
    if(is_depth_texture)
    {
        float distance = linear_depth_to_depth(fs_output.x);
        fs_output.xyz = vec3(distance);
    }

    // Test
    // float font_alpha = pow(clamp(smoothstep(0.97, 1.0, pow(1.0 - fs_output.x, 0.5)), 0.0, 1.0), 1.0);

    fs_output.a = 1.0;
}
#endif // FRAGMENT_SHADER