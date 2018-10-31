#include "scene_constants.glsl"
#include "utility.glsl"

uniform uint max_count;
uniform uint spawn_count;

#ifdef COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer update_particle_counter_buffer { uint update_particle_counter; };
layout(std430, binding=1) buffer draw_indirect_buffer { DrawElementsIndirectCommand draw_indirect; };

void main()
{
    update_particle_counter = min(PARTICLE_MAX_COUNT, update_particle_counter);

    draw_indirect.instance_count = update_particle_counter;
}
#endif
