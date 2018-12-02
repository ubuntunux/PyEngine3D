#include "scene_constants.glsl"

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
};

uniform vec4 pos_size;

#ifdef VERTEX_SHADER
layout (location = 0) in vec4 vs_in_position;
layout (location = 0) out VERTEX_OUTPUT vs_output;

void main()
{
    vec4 pos_size_info = pos_size / SCREEN_SIZE.xyxy;

    vs_output.position = vs_in_position.xyz;
    vs_output.tex_coord = vs_in_position.xy * 0.5 + 0.5;
    gl_Position = vs_in_position;

    gl_Position.xy = gl_Position.xy * pos_size_info.zw - (1.0 - pos_size_info.zw) + pos_size_info.xy * 2.0;

}
#endif // VERTEX_SHADER