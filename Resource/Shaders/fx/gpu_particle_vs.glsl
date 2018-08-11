#include "scene_constants.glsl"

uniform sampler2D texture_diffuse;


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
layout (location = 5) flat out uint instanceID;


void main()
{
    instanceID = gl_InstanceID.x;
    vec3 vertex_normal = normalize(vs_in_normal);
    vec3 vertex_tangent = normalize(vs_in_tangent);
    mat4 local_matrix_origin = emitter_datas[instanceID].local_matrix;
    vec3 local_position = local_matrix_origin[3].xyz:
    local_matrix_origin[3].xyz = vec3(0.0);
    mat4 local_to_world = EMITTER_BILLBOARD ? INV_VIEW_ORIGIN * local_matrix_origin : EMITTER_PARENT_MATRIX * local_matrix_origin;
    vec4 vertex_position = vec4(vs_in_position, 1.0);
    vec4 world_position = EMITTER_PARENT_MATRIX * vec4(local_position.xyz, 1.0);
    world_position += local_to_world * vertex_position;

    vs_output.world_position = world_position.xyz;

    vec2 uv_size = vs_in_tex_coord.xy / vec2(EMITTER_CELL_COUNT);
    vs_output.uv = emitter_datas[instanceID].sequence_uv + uv_size;
    vs_output.next_uv = emitter_datas[instanceID].next_sequence_uv + uv_size;
    vs_output.sequence_ratio = emitter_datas[instanceID].sequence_ratio;
    vs_output.opacity = emitter_datas[instanceID].opacity;

    gl_Position = VIEW_PROJECTION * world_position;
}
#endif
