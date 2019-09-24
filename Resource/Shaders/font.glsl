#include "scene_constants.glsl"

uniform sampler2D texture_font;
uniform float font_size;
uniform vec2 offset;
uniform vec2 inv_canvas_size;
uniform float count_of_side;

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec2 font_offset;
};

#ifdef VERTEX_SHADER
layout (location = 0) in vec4 vs_in_position;
layout (location = 1) in vec4 vs_in_font_infos;    // instancing data

layout (location = 0) out VERTEX_OUTPUT vs_output;

void main()
{
    vec2 inv_texture_size = 1.0 / textureSize(texture_font, 0).xy;
    vec2 font_texcoord_size = 1.0 / count_of_side - inv_texture_size;

    vec2 ratio = vec2(font_size) * inv_canvas_size;
    vec2 texcoord = vs_in_position.xy * 0.5 + 0.5;

    vs_output.tex_coord = vs_in_font_infos.zw + texcoord * font_texcoord_size + inv_texture_size * 0.5;

    float column = vs_in_font_infos.x;
    float row = vs_in_font_infos.y;
    vec2 position;
    position.x = (column + texcoord.x) * font_size * inv_canvas_size.x;
    position.y = (texcoord.y - row) * font_size * inv_canvas_size.y;
    position.xy += offset * inv_canvas_size.xy;

    gl_Position = vec4(position * 2.0 - 1.0, 0.0, 1.0);
}
#endif


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    fs_output.xyz = vec3(1.0);
    fs_output.w = pow(texture2D(texture_font, vs_output.tex_coord).x, 0.1);
    //fs_output.w = smoothstep(0.0, 1.0, fs_output.w);
}
#endif