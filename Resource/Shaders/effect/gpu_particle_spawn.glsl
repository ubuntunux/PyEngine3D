#include "scene_constants.glsl"
#include "utility.glsl"


#ifdef COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer particle_buffer { ParticleData particle_datas[]; };
layout( binding=1 ) uniform atomic_uint particle_counter;
layout( binding=2 ) uniform atomic_uint particle_spawn_counter;
layout(std430, binding=3) buffer particle_alive_buffer { uint particle_alive_datas[]; };
layout(std430, binding=4) buffer particle_dead_buffer { uint particle_dead_datas[]; };


void main()
{
    uint id = gl_GlobalInvocationID.x;
    atomicCounterExchange(particle_spawn_counter, 3);
    atomicCounterAdd(particle_counter, 3);
}
#endif
