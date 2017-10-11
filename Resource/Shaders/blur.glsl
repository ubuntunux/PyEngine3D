#version 430 core

#include "quad.glsl"

uniform float blur_radius;
uniform sampler2D texture_diffuse;

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;
void main() {
    vec2 texcoord = vs_output.texcoord.xy;
    vec2 scale = 1.0 / textureSize(texture_diffuse, 0);

    fs_output = vec4(0.0, 0.0, 0.0, 1.0);

    float weight = 0.0;

    for( float y = -blur_radius; y <= blur_radius; y++ )
    {
        for( float x = -blur_radius; x <= blur_radius; x++ )
        {
            fs_output += texture(texture_diffuse, texcoord + vec2(x, y) * scale);
            weight += 1.0;
        }
    }

    fs_output /= weight;
}
#endif // FRAGMENT_SHADER