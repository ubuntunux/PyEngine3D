#include "scene_constants.glsl"

uniform mat4 particle_matrix;

struct VERTEX_OUTPUT
{
    vec3 world_position;
    vec2 uv;
};

layout(std430, binding=0) buffer InputPos { vec3 pos[]; };

#ifdef GL_VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;


layout (location = 0) out VERTEX_OUTPUT vs_output;

void main() {
    vec3 vertex_normal = normalize(vs_in_normal);
    vec3 vertex_tangent = normalize(vs_in_tangent);
    mat4 world_matrix = particle_matrix * INV_VIEW_ORIGIN;
    vec4 vertex_position = vec4(vs_in_position, 1.0);

    vec4 world_position = world_matrix * vertex_position;
    world_position.xyz += pos[gl_InstanceID];
    vs_output.world_position = world_position.xyz;
    vs_output.uv = vs_in_tex_coord;

    gl_Position = VIEW_PROJECTION * world_position;
}
#endif