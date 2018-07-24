#include "scene_constants.glsl"

uniform sampler2D texture_diffuse;

uniform bool billboard;
uniform vec3 color;
uniform int blend_mode;
uniform mat4 particle_matrix;
uniform float sequence_width;
uniform float sequence_height;


struct VERTEX_OUTPUT
{
    vec3 world_position;
    vec2 uv;
    vec2 next_uv;
    float sequence_ratio;
    float opacity;
};

layout(std430, binding=0) buffer emitter_buffer { EmitterData emitter_datas[]; };

#ifdef GL_VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;


layout (location = 0) out VERTEX_OUTPUT vs_output;

void main()
{
    uint id = gl_InstanceID.x;
    vec3 vertex_normal = normalize(vs_in_normal);
    vec3 vertex_tangent = normalize(vs_in_tangent);
    mat4 world_matrix = particle_matrix * INV_VIEW_ORIGIN;
    vec4 vertex_position = vec4(vs_in_position, 1.0);

    vec4 world_position = world_matrix * vertex_position;
    world_position.xyz += emitter_datas[id].position.xyz;
    vs_output.world_position = world_position.xyz;

    vec2 uv_size = vs_in_tex_coord.xy / vec2(EMITTER_CELL_COUNT);
    vs_output.uv = emitter_datas[id].sequence_uv + uv_size;
    vs_output.next_uv = emitter_datas[id].next_sequence_uv + uv_size;
    vs_output.sequence_ratio = emitter_datas[id].sequence_ratio;

    if(EMITTER_STATE_ALIVE == emitter_datas[id].state)
    {
        vs_output.opacity = emitter_datas[id].opacity;
    }
    else
    {
        vs_output.opacity = 0.0;
    }

    gl_Position = VIEW_PROJECTION * world_position;
}
#endif