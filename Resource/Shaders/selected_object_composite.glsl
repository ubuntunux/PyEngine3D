#include "utility.glsl"
#include "quad.glsl"

uniform sampler2D texture_mask;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    fs_output = vec4(0.0, 0.0, 0.0, 1.0);
    vec2 tex_coord = vs_output.tex_coord.xy;
    vec2 inv_texture_size = 1.0 / textureSize(texture_mask, 0);
    float center_mask = texture2D(texture_mask, tex_coord).x;
    float mask = 0.0;

    for(int y=-2; y<=2; ++y)
    {
        for(int x=-2; x<=2; ++x)
        {
            if(x == 0 && y == 0)
            {
                continue;
            }

            mask = max(mask, texture2D(texture_mask, tex_coord + vec2(x, y) * inv_texture_size).x);
        }
    }

    mask = saturate(mask - center_mask) + center_mask * 0.5;
    fs_output = vec4(0.5, 0.5, 1.0, 1.0) * mask;
}
#endif // FRAGMENT_SHADER