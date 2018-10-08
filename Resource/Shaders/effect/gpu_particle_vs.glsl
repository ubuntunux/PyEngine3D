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

layout(std430, binding=0) buffer particle_buffer { ParticleData particle_datas[]; };

#ifdef VERTEX_SHADER
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
    vec4 vertex_position = vec4(vs_in_position, 1.0);

    mat4 world_matrix;
    vec3 world_position;

    // TODO : Move calculation part of the local position to compute shader
    if(PARTICLE_BILLBOARD)
    {
        world_matrix = particle_datas[instanceID].local_matrix;
        world_matrix[3].xyz = vec3(0.0);
        world_matrix = INV_VIEW_ORIGIN * world_matrix;

        vec3 local_position = (particle_datas[instanceID].parent_matrix * particle_datas[instanceID].local_matrix)[3].xyz;
        world_position = local_position + (world_matrix * vertex_position).xyz;
    }
    else
    {
        world_matrix = particle_datas[instanceID].parent_matrix * particle_datas[instanceID].local_matrix;
        world_position = (world_matrix * vertex_position).xyz;
    }

    vs_output.world_position = world_position.xyz;

    vec2 uv_size = vs_in_tex_coord.xy / vec2(PARTICLE_CELL_COUNT);
    vs_output.uv = particle_datas[instanceID].sequence_uv + uv_size;
    vs_output.next_uv = particle_datas[instanceID].next_sequence_uv + uv_size;
    vs_output.sequence_ratio = particle_datas[instanceID].sequence_ratio;
    vs_output.opacity = particle_datas[instanceID].opacity;

    gl_Position = VIEW_PROJECTION * vec4(world_position, 1.0);
}
#endif
