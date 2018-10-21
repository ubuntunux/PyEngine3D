#include "scene_constants.glsl"
#include "utility.glsl"


#ifdef COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer alive_particle_counter_buffer { uint alive_particle_counter; };
layout(std430, binding=1) buffer alive_particle_index_buffer { uint alive_particle_index[]; };
layout(std430, binding=2) buffer update_particle_counter_buffer { uint update_particle_counter; };
layout(std430, binding=3) buffer update_particle_index_buffer { uint update_particle_index[]; };

void main()
{
    uint id = gl_GlobalInvocationID.x;
    alive_particle_counter = 0;
    alive_particle_index[id] = id;
    update_particle_counter = 0;
    update_particle_index[id] = id;
}
#endif
