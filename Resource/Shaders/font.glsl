#version 430 core

uniform sampler2D texture_font;
uniform float font_size;
uniform vec2 screen_size;
uniform float count_horizontal;

struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 tex_coord;
    layout(location=5) vec4 font_offset;
};

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
    vec4 font_offset;
};

#ifdef VERTEX_SHADER
in VERTEX_INPUT vs_input;
out VERTEX_OUTPUT vs_output;

void main() {
    vs_output.tex_coord = vs_input.tex_coord / count_horizontal;
    vec2 ratio = vec2(font_size) / screen_size;
    vec2 position = (vs_input.position.xy * 0.5 + 0.5) * ratio + vs_input.font_offset.xy / screen_size;
    gl_Position = vec4(position * 2.0 - 1.0, 0.0, 1.0);
    vs_output.position = gl_Position.xyz;
    vs_output.font_offset = vs_input.font_offset;
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