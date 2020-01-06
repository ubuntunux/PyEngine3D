#include "ui/ui_quad.glsl"

uniform sampler2D texture_diffuse;
uniform bool is_render_diffuse;
uniform vec4 color;
uniform vec4 texcoord;
uniform float opacity;


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec4 result = color;

    vec2 uv = mix(texcoord.xy, texcoord.zw, vs_output.tex_coord.xy);

    if(is_render_diffuse)
    {
        if(0.0 < uv.x && 0.0 < uv.y && uv.x < 1.0 && uv.y < 1.0)
        {
            vec4 diffuse = texture2D(texture_diffuse, uv);
            result = mix(diffuse, diffuse * color, color.w);
        }
    }

    result.w *= opacity;

    fs_output = result;
}
#endif