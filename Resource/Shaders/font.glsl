uniform sampler2D texture_font;
uniform float font_size;
uniform vec2 screen_size;
uniform float count_horizontal;

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec4 font_offset;
};

#ifdef VERTEX_SHADER
layout (location = 0) in vec4 vs_in_position;
layout (location = 1) in vec4 vs_in_font_offset;    // instancing data

layout (location = 0) out VERTEX_OUTPUT vs_output;

void main() {
    vec2 inv_screen_size = 1.0 / screen_size;
    vec2 ratio = vec2(font_size) * inv_screen_size;
    vec2 texcoord = vs_in_position.xy * 0.5 + 0.5;
    vec2 position = texcoord * ratio + vs_in_font_offset.xy * inv_screen_size;
    vs_output.tex_coord = texcoord / count_horizontal;
    vs_output.font_offset = vs_in_font_offset;
    gl_Position = vec4(position * 2.0 - 1.0, 0.0, 1.0);
}
#endif


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    fs_output.xyz = vec3(1.0);
    fs_output.w = 2.0 * texture2D(texture_font, vs_output.font_offset.zw + vs_output.tex_coord).x;
    //fs_output = vec4(smoothstep(0.99, 1.0, fs_output.x));
}
#endif