#include "scene_constants.glsl"
#include "utility.glsl"
#include "effect/common.glsl"

uniform uint max_count;
uniform uint spawn_count;

#ifdef COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer index_range_buffer { ParticleIndexRange particle_index_range; };
layout(std430, binding=1) buffer draw_indirect_buffer { DrawElementsIndirectCommand draw_indirect; };

void main()
{
    particle_index_range.begin_index = (particle_index_range.begin_index + particle_index_range.destroy_count) % PARTICLE_MAX_COUNT;

    if(particle_index_range.instance_count < particle_index_range.destroy_count)
    {
        particle_index_range.instance_count = 0;
    }
    else
    {
        particle_index_range.instance_count -= particle_index_range.destroy_count;
    }
    particle_index_range.destroy_count = 0;

    draw_indirect.instance_count = particle_index_range.instance_count;
}
#endif
