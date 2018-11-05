#include "scene_constants.glsl"
#include "utility.glsl"
#include "effect/common.glsl"

uniform uint max_count;
uniform uint spawn_count;

#ifdef COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer index_range_buffer { ParticleIndexRange particle_index_range; };
layout(std430, binding=1) buffer dispatch_indirect_buffer { DispatchIndirectCommand dispatch_indirect; };

void main()
{
    particle_index_range.instance_count = min(PARTICLE_MAX_COUNT, particle_index_range.instance_count + PARTICLE_SPAWN_COUNT);
    particle_index_range.destroy_count = 0;

    dispatch_indirect.num_groups_x = (particle_index_range.instance_count + WORK_GROUP_SIZE - 1) / WORK_GROUP_SIZE;
    dispatch_indirect.num_groups_y = 1;
    dispatch_indirect.num_groups_z = 1;
}
#endif
