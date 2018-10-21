#include "scene_constants.glsl"
#include "utility.glsl"

uniform uint max_count;
uniform uint spawn_count;

#ifdef COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer alive_particle_counter_buffer
{
    uint alive_particle_counter;
};

layout(std430, binding=1) buffer update_particle_counter_buffer
{
    uint update_particle_counter;
};

layout(std430, binding=2) buffer dead_particle_counter_buffer
{
    uint dead_particle_counter;
};

layout(std430, binding=3) buffer dispatch_indirect_buffer
{
    DispatchIndirectCommand dispatch_indirect;
};

void main()
{
    alive_particle_counter = min(PARTICLE_MAX_COUNT, alive_particle_counter + PARTICLE_SPAWN_COUNT);
    dispatch_indirect.num_groups_x = alive_particle_counter;

    // reset
    update_particle_counter = 0;
    dead_particle_counter = 0;
}
#endif
