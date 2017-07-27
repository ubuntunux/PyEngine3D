#version 430 core

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
        // depth normalize
        fs_output.xyz = vec3(log(1.0 / (1.0 - fs_output.x)) * 0.1);
    }
}
#endif // FRAGMENT_SHADER