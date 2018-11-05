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
    float t0 = TIME;
    float t1 = rand(vec2(t0, random_seed));
    float t2 = rand(vec2(t0, t1));
    float t3 = rand(vec2(t0, t2));
    float t4 = rand(vec2(t0, t3));
    float t5 = rand(vec2(t0, t4));
    float t6 = rand(vec2(t0, t5));
    float t7 = rand(vec2(t0, t6));
    float t8 = rand(vec2(t0, t7));
    float t9 = rand(vec2(t0, t8));
    float t10 = rand(vec2(t0, t9));
    float t11 = rand(vec2(t0, t10));
    float t12 = rand(vec2(t0, t11));
    float t13 = rand(vec2(t0, t12));
    float t14 = rand(vec2(t0, t13));
    float t15 = rand(vec2(t0, t14));
    float t16 = rand(vec2(t0, t15));
    float t17 = rand(vec2(t0, t16));
    float t18 = rand(vec2(t0, t17));
    float t19 = rand(vec2(t0, t18));
    float t20 = rand(vec2(t0, t19));

    particle_data.delay = mix(PARTICLE_DELAY.x, PARTICLE_DELAY.y, t1);
    particle_data.state = (0.0 < particle_data.delay) ? PARTICLE_STATE_DELAY : PARTICLE_STATE_ALIVE;
    particle_data.life_time = mix(PARTICLE_LIFE_TIME.x, PARTICLE_LIFE_TIME.y, t2);
    particle_data.transform_position = mix(PARTICLE_TRANSFORM_POSITION_MIN, PARTICLE_TRANSFORM_POSITION_MAX, vec3(t3, t4, t5));
    particle_data.transform_rotation = mix(PARTICLE_TRANSFORM_ROTATION_MIN, PARTICLE_TRANSFORM_ROTATION_MAX, vec3(t9, t10, t11));
    particle_data.transform_scale = mix(PARTICLE_TRANSFORM_SCALE_MIN, PARTICLE_TRANSFORM_SCALE_MAX, vec3(t15, t16, t17));
    particle_data.velocity_position = mix(PARTICLE_VELOCITY_POSITION_MIN, PARTICLE_VELOCITY_POSITION_MAX, vec3(t6, t7, t8));
    particle_data.velocity_rotation = mix(PARTICLE_VELOCITY_ROTATION_MIN, PARTICLE_VELOCITY_ROTATION_MAX, vec3(t12, t13, t14));
    particle_data.velocity_scale = mix(PARTICLE_VELOCITY_SCALE_MIN, PARTICLE_VELOCITY_SCALE_MAX, vec3(t18, t19, t20));
    particle_data.opacity = PARTICLE_OPACITY;
    particle_data.parent_matrix = PARTICLE_PARENT_MATRIX;
    // We will apply inverse_matrix here because we will apply parent_matrix later.
    particle_data.force = (PARTICLE_PARENT_INVERSE_MATRIX * vec4(0.0, -PARTICLE_FORCE_GRAVITY, 0.0, 1.0)).xyz;
    particle_data.local_matrix = mat4(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0);

    particle_data.elapsed_time = 0.0;
    particle_data.sequence_ratio = 0.0;
    particle_data.sequence_index = 0;
    particle_data.next_sequence_index = 0;
}

void main()
{
    uint available_spawn_count = min(PARTICLE_SPAWN_COUNT, PARTICLE_MAX_COUNT - particle_index_range.instance_count);

    if(gl_GlobalInvocationID.x < available_spawn_count)
    {
        uint id = (particle_index_range.begin_index + particle_index_range.instance_count + gl_GlobalInvocationID.x) % PARTICLE_MAX_COUNT;
        spawn_particle(particle_datas[id], float(id) * 0.01 + PI);
    }
}
#endif
