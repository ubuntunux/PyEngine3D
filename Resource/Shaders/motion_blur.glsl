#version 430 core

#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_velocity;

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    vec2 texcoord = vs_output.texcoord.xy;

    vec4 color = texture(texture_diffuse, texcoord);
    float weights = 1.0;
    const int kernel = 8;
    const vec2 inv_texture_size = 1.0 / textureSize(texture_velocity, 0);
    for(int y=-kernel;y<=kernel;++y)
    {
        for(int x=-kernel;x<=kernel;++x)
        {
            float weight = 0.0;
            vec2 uv = texcoord + vec2(x, y) * inv_texture_size;
            vec2 velocity = texture(texture_velocity, uv).xy * 50.0;

            weight = clamp(-dot(velocity, normalize(uv - texcoord)), 0.0, 1.0);
            color += texture(texture_diffuse, uv) * weight;
            weights += weight;
        }
    }

    fs_output.xyz = color.xyz / vec3(weights);
    fs_output.a = 1.0;
}
#endif // FRAGMENT_SHADER