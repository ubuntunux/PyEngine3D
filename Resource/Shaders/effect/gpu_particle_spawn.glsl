#include "scene_constants.glsl"
#include "utility.glsl"

uniform uint spawn_count;

#ifdef COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer alive_particle_counter_buffer
{
    uint alive_particle_counter;
};

layout(std430, binding=1) buffer alive_particle_index_buffer
{
    uint alive_particle_index[];
};

layout(std430, binding=2) buffer dead_particle_index_buffer
{
    uint dead_particle_index[];
};

layout(std430, binding=3) buffer particle_buffer
{
    ParticleData particle_datas[];
};


void main()
{
    uint index = alive_particle_counter + gl_GlobalInvocationID.x;

    if(PARTICLE_MAX_COUNT <= index)
    {
        return;
    }

    uint id = dead_particle_index[index];
    alive_particle_index[index] = id;
    particle_datas[id].state = PARTICLE_STATE_NONE;
}
#endif
