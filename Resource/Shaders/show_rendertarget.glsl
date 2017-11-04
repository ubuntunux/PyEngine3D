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
    fs_output = texture(texture_source, vs_output.tex_coord.xy * 5.3);
    if(is_depth_texture)
    {
        float distance = linear_depth_to_depth(fs_output.x);
        fs_output.xyz = vec3(distance);
    }

    // Test Distance Field Font
    // float font_alpha = smoothstep(0.95, 1.0, fs_output.x);
    // fs_output.xyz = vec3(font_alpha);

    fs_output.a = 1.0;
}
#endif // FRAGMENT_SHADER