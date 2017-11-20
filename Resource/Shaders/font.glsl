#version 430 core

uniform sampler2D texture_font;
uniform float font_size;
uniform vec2 screen_size;
uniform float count_horizontal;

struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 font_offset;    // instancing data
};

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec4 font_offset;
};

#ifdef VERTEX_SHADER
in VERTEX_INPUT vs_input;
out VERTEX_OUTPUT vs_output;

void main() {
    vec2 ratio = vec2(font_size) / screen_size;
    vec2 texcoord = vs_input.position.xy * 0.5 + 0.5;
    vec2 position = texcoord * ratio + vs_input.font_offset.xy / screen_size;
    vs_output.tex_coord = texcoord / count_horizontal;
    vs_output.font_offset = vs_input.font_offset;
    gl_Position = vec4(position * 2.0 - 1.0, 0.0, 1.0);
}
#endif


#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    fs_output.xyz = vec3(1.0);
    fs_output.w = 2.0 * texture(texture_font, vs_output.font_offset.zw + vs_output.tex_coord).x;
    //fs_output = vec4(smoothstep(0.99, 1.0, fs_output.x));
}
#endif