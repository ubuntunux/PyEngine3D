#include "scene_constants.glsl"

uniform bool is_debug_line_2d;
uniform vec3 position0;
uniform vec3 position1;
uniform vec4 color;
uniform float width;

#ifdef VERTEX_SHADER
layout (location = 0) in vec4 vs_in_position;

void main() {
    vec4 vertex_position0 = vec4(position0, 1.0);
    vec4 vertex_position1 = vec4(position1, 1.0);

    if(false == is_debug_line_2d)
    {
        vertex_position0 = VIEW_PROJECTION * vec4(position0.xyz, 1.0);
        vertex_position1 = VIEW_PROJECTION * vec4(position1.xyz, 1.0);

        vertex_position0.xyz /= vertex_position0.w;
        vertex_position1.xyz /= vertex_position1.w;
    }

    vec2 lineWidth = normalize(vertex_position1.xy - vertex_position0.xy);
    lineWidth = vec2(-lineWidth.y, lineWidth.x);

    gl_Position = mix(vertex_position0, vertex_position1, clamp(vs_in_position.y * 0.5 + 0.5, 0.0, 1.0));
    gl_Position.xy += mix(lineWidth, -lineWidth, clamp(vs_in_position.x * 0.5 + 0.5, 0.0, 1.0)) / SCREEN_SIZE.xy * width;

    if(is_debug_line_2d)
    {
        gl_Position.z = -1.0;
        gl_Position.w = 1.0;
    }
    else
    {
        gl_Position.xyz *= gl_Position.w;
    }
}

#endif // VERTEX_SHADER

#ifdef FRAGMENT_SHADER
layout (location = 0) out vec4 fs_output;

void main() {
    fs_output = color;
    fs_output.w = clamp(fs_output.w, 0.0, 1.0);
}
#endif // FRAGMENT_SHADER