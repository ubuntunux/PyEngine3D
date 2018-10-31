#include "scene_constants.glsl"
#include "utility.glsl"


#ifdef COMPUTE_SHADER
layout(local_size_x=WORK_GROUP_SIZE, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer alive_particle_counter_buffer { uint alive_particle_counter; };
layout(std430, binding=1) buffer update_particle_counter_buffer { uint update_particle_counter; };
layout(std430, binding=2) buffer particle_index_buffer { uint particle_index[]; };

void main()
{
    if(gl_GlobalInvocationID.x < PARTICLE_MAX_COUNT)
    {
        uint id = gl_GlobalInvocationID.x;
        alive_particle_counter = 0;
        particle_index[id] = id;
        update_particle_counter = 0;
    }
}
#endif
