#include "scene_constants.glsl"
#include "effect/common.glsl"

uniform sampler2D texture_diffuse;

layout(std430, binding=0) buffer particle_buffer { ParticleData particle_datas[]; };
layout(std430, binding=1) buffer index_range_buffer { ParticleIndexRange particle_index_range; };

struct VERTEX_OUTPUT
{
    vec3 world_position;
    vec2 uv;
    vec2 next_uv;
    float sequence_ratio;
    float opacity;
};


#define INSTANCE_ID_LOCATION 5


#ifdef VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;

layout (location = 0) out VERTEX_OUTPUT vs_output;
layout (location = INSTANCE_ID_LOCATION) flat out uint instanceID;


void main()
{
    instanceID = gl_InstanceID.x;

    uint id = (particle_index_range.begin_index + gl_InstanceID.x) % PARTICLE_MAX_COUNT;

    if(PARTICLE_STATE_ALIVE != particle_datas[id].state)
    {
        // culling
        gl_Position = vec4(0.0, 0.0, -10.0, 1.0);
        return;
    }

    vec3 vertex_normal = normalize(vs_in_normal);
    vec3 vertex_tangent = normalize(vs_in_tangent);
    vec4 vertex_position = vec4(vs_in_position, 1.0);

    vec3 world_position = particle_datas[id].relative_position.xyz + CAMERA_POSITION.xyz;
    world_position += (particle_datas[id].local_matrix * vertex_position).xyz;

    vs_output.world_position = world_position.xyz;

    vec2 uv_size = vs_in_tex_coord.xy / vec2(PARTICLE_CELL_COUNT);
    vs_output.uv = particle_datas[id].sequence_uv + uv_size;
    vs_output.next_uv = particle_datas[id].next_sequence_uv + uv_size;
    vs_output.sequence_ratio = particle_datas[id].sequence_ratio;
    vs_output.opacity = particle_datas[id].opacity;

    gl_Position = VIEW_PROJECTION * vec4(world_position, 1.0);
}
#endif
