#include "scene_constants.glsl"
#include "utility.glsl"
#include "effect/common.glsl"

uniform uint spawn_count;

#ifdef COMPUTE_SHADER
layout(local_size_x=WORK_GROUP_SIZE, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer index_range_buffer { ParticleIndexRange particle_index_range; };
layout(std430, binding=1) buffer particle_buffer { ParticleData particle_datas[]; };


void spawn_particle(inout ParticleData particle_data, float random_seed)
{
    vec4 random_factor = generate_random(random_seed);

    particle_data.state = (0.0 < particle_data.delay) ? PARTICLE_STATE_DELAY : PARTICLE_STATE_ALIVE;
    particle_data.delay = mix(PARTICLE_DELAY.x, PARTICLE_DELAY.y, random_factor.x);
    particle_data.life_time = mix(PARTICLE_LIFE_TIME.x, PARTICLE_LIFE_TIME.y, random_factor.y);

    vec3 spawn_position = vec3(0.0);

    generate_random4(random_factor);

    const uint spawn_volume_type = PARTICLE_SPAWN_VOLUME_TYPE & 0x000000FF;
    const uint spawn_volume_abs_axis = PARTICLE_SPAWN_VOLUME_TYPE & 0xFFFFFF00;

    if(SPAWN_VOLUME_BOX == spawn_volume_type)
    {
        spawn_position = PARTICLE_SPAWN_VOLUME_INFO.xyz * (random_factor.xyz - 0.5);
    }
    else if(SPAWN_VOLUME_SPHERE == spawn_volume_type)
    {
        vec3 dir = safe_normalize(random_factor.xyz - 0.5);
        spawn_position = dir * mix(PARTICLE_SPAWN_VOLUME_INFO.y, PARTICLE_SPAWN_VOLUME_INFO.x, random_factor.w * random_factor.w) * 0.5;
    }
    else if(SPAWN_VOLUME_CONE == spawn_volume_type)
    {
        vec2 dir = safe_normalize(random_factor.xy - 0.5);
        float ratio = random_factor.z * random_factor.z;
        spawn_position.y = PARTICLE_SPAWN_VOLUME_INFO.z * (ratio - 0.5);
        spawn_position.xz = dir * mix(PARTICLE_SPAWN_VOLUME_INFO.y, PARTICLE_SPAWN_VOLUME_INFO.x, ratio) * sqrt(random_factor.w) * 0.5;
    }
    else if(SPAWN_VOLUME_CYLINDER == spawn_volume_type)
    {
        vec2 dir = safe_normalize(random_factor.xy - 0.5);
        spawn_position.y = PARTICLE_SPAWN_VOLUME_INFO.z * (random_factor.z - 0.5);
        spawn_position.xz = dir * mix(PARTICLE_SPAWN_VOLUME_INFO.y, PARTICLE_SPAWN_VOLUME_INFO.x, random_factor.w * random_factor.w) * 0.5;
    }

    spawn_position.x = (0 != (spawn_volume_abs_axis & (1 << 8))) ? abs(spawn_position.x) : spawn_position.x;
    spawn_position.y = (0 != (spawn_volume_abs_axis & (1 << 9))) ? abs(spawn_position.y) : spawn_position.y;
    spawn_position.z = (0 != (spawn_volume_abs_axis & (1 << 10))) ? abs(spawn_position.z) : spawn_position.z;

    particle_data.transform_position = (PARTICLE_SPAWN_VOLUME_MATRIX * vec4(spawn_position, 1.0)).xyz;

    generate_random3(random_factor);
    particle_data.transform_rotation = mix(PARTICLE_TRANSFORM_ROTATION_MIN, PARTICLE_TRANSFORM_ROTATION_MAX, random_factor.xyz);

    generate_random3(random_factor);
    particle_data.transform_scale = mix(PARTICLE_TRANSFORM_SCALE_MIN, PARTICLE_TRANSFORM_SCALE_MAX, random_factor.xyz);

    generate_random3(random_factor);
    particle_data.velocity_position = mix(PARTICLE_VELOCITY_POSITION_MIN, PARTICLE_VELOCITY_POSITION_MAX, random_factor.xyz);

    if(VELOCITY_TYPE_SPAWN_DIRECTION == PARTICLE_VELOCITY_TYPE)
    {
        particle_data.velocity_position = abs(particle_data.velocity_position) * safe_normalize(particle_data.transform_position);
    }
    else if(VELOCITY_TYPE_HURRICANE == PARTICLE_VELOCITY_TYPE)
    {
        particle_data.velocity_position = abs(particle_data.velocity_position) * cross(vec3(0.0, 1.0, 0.0), safe_normalize(particle_data.transform_position));
    }

    generate_random3(random_factor);
    particle_data.velocity_rotation = mix(PARTICLE_VELOCITY_ROTATION_MIN, PARTICLE_VELOCITY_ROTATION_MAX, random_factor.xyz);

    generate_random3(random_factor);
    particle_data.velocity_scale = mix(PARTICLE_VELOCITY_SCALE_MIN, PARTICLE_VELOCITY_SCALE_MAX, random_factor.xyz);

    particle_data.opacity = PARTICLE_OPACITY;
    particle_data.parent_matrix = PARTICLE_PARENT_MATRIX;

    // We will apply inverse_matrix here because we will apply parent_matrix later.
    particle_data.force = transpose(mat3(PARTICLE_PARENT_MATRIX)) * vec3(0.0, -PARTICLE_FORCE_GRAVITY, 0.0);
    particle_data.local_matrix = mat4(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0);

    particle_data.elapsed_time = 0.0;
    particle_data.sequence_ratio = 0.0;
    particle_data.sequence_index = 0;
    particle_data.next_sequence_index = 0;

    particle_data.relative_position = vec3(0.0, 0.0, 0.0);
}

void main()
{
    uint available_spawn_count = min(PARTICLE_SPAWN_COUNT, PARTICLE_MAX_COUNT - particle_index_range.instance_count);

    if(gl_GlobalInvocationID.x < available_spawn_count)
    {
        uint id = (particle_index_range.begin_index + particle_index_range.instance_count + gl_GlobalInvocationID.x) % PARTICLE_MAX_COUNT;
        spawn_particle(particle_datas[id], float(id) / float(PARTICLE_MAX_COUNT) + PI);
    }
}
#endif
