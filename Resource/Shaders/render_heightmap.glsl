#include "scene_constants.glsl"
#include "utility.glsl"

uniform vec3 bound_box_min;
uniform vec3 bound_box_max;
uniform mat4 model;

struct VERTEX_OUTPUT
{
    vec3 world_position;
};

#ifdef VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;

layout (location = 0) out VERTEX_OUTPUT vs_output;

void main() {
    vec3 world_position = (model * vec4(vs_in_position, 1.0)).xyz;
    vs_output.world_position = world_position;
    gl_Position = vec4(world_position, 1.0);
    gl_Position.xyz = (gl_Position.xyz - bound_box_min) / (bound_box_max - bound_box_min);
    gl_Position.xy = gl_Position.xz * 2.0 - 1.0;
    gl_Position.z = 0.0;
}
#endif


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out float fs_ouptut;

void main()
{
    fs_ouptut = (vs_output.world_position.y - bound_box_min.y) / (bound_box_max.y - bound_box_min.y);
}
#endif