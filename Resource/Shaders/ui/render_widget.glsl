#include "ui/ui_quad.glsl"

uniform sampler2D texture_diffuse;
uniform bool is_render_diffuse;
uniform vec4 color;


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec4 result = color;

    vec2 tex_coord = vs_output.tex_coord.xy;

    if(is_render_diffuse)
    {
        if(0.0 < tex_coord.x && 0.0 < tex_coord.y && tex_coord.x < 1.0 && tex_coord.y < 1.0)
        {
            result = texture2D(texture_diffuse, tex_coord);
            result = mix(result, result * color, color.w);
        }
    }

    fs_output = result;
}
#endif