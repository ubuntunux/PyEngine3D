#include "quad.glsl"

uniform float blur_kernel_radius;
uniform sampler2D texture_diffuse;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;
    vec2 scale = 1.0 / textureSize(texture_diffuse, 0);

    fs_output = vec4(0.0, 0.0, 0.0, 1.0);

    float weight = 0.0;

    float radius = sqrt(2.0) * blur_kernel_radius + 0.125;

    for( float y = -blur_kernel_radius; y <= blur_kernel_radius; y++ )
    {
        for( float x = -blur_kernel_radius; x <= blur_kernel_radius; x++ )
        {
            float wg = pow(1.0 - length(vec2(x, y)) / radius, 3.0);
            fs_output += texture2D(texture_diffuse, tex_coord + vec2(x, y) * scale) * wg;
            weight += wg;
        }
    }

    fs_output /= weight;
}
#endif // FRAGMENT_SHADER