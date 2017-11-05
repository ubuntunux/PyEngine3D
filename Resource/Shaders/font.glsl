#version 430 core

uniform sampler2D texture_font;
uniform vec2 vertex_scale;
uniform float texcoord_scale;
uniform vec4 font_offset;

struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 tex_coord;
};

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
};

#ifdef VERTEX_SHADER
in VERTEX_INPUT vs_input;
out VERTEX_OUTPUT vs_output;

void main() {
    vs_output.tex_coord = vs_input.tex_coord * texcoord_scale;
    vs_output.position = vs_input.position;
    vs_output.position.xy = (font_offset.xy * 2.0 - 1.0) + vs_output.position.xy * vertex_scale;
    gl_Position = vec4(vs_input.position, 1.0);
}
#endif


#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    fs_output.xyz = vec3(texture(texture_font, vs_output.tex_coord).x);
    fs_output.a = 1.0;
}
#endif