#include "scene_constants.glsl"

uniform bool is_debug_line_2d;
uniform vec3 position0;
uniform vec3 position1;
uniform vec4 color;

#ifdef VERTEX_SHADER
layout (location = 0) in vec4 vs_in_position;

void main() {
    vec3 vertex_position = (0 == gl_VertexID) ? position0.xyz : position1.xyz;

    if(is_debug_line_2d)
    {
        gl_Position.xyz = vertex_position;
        gl_Position.z = -1.0;
        gl_Position.w = 1.0;
    }
    else
    {
        gl_Position = VIEW_PROJECTION * vec4(vertex_position.xyz, 1.0);
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