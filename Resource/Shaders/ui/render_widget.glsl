#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform bool is_render_diffuse;
uniform vec4 background_color;


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    fs_output = vec4(0.0);

    vec2 tex_coord = vs_output.tex_coord.xy;

    if(is_render_diffuse)
    {
        fs_output = texture2D(texture_diffuse, tex_coord);
    }

}
#endif