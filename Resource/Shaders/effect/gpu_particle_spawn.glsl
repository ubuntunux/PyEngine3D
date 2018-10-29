#include "scene_constants.glsl"
#include "utility.glsl"

uniform uint spawn_count;

#ifdef COMPUTE_SHADER
layout(local_size_x=WORK_GROUP_SIZE, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer alive_particle_counter_buffer { uint alive_particle_counter; };
layout(std430, binding=1) buffer alive_particle_index_buffer { uint alive_particle_index[]; };
layout(std430, binding=2) buffer particle_buffer { ParticleData particle_datas[]; };

void spawn_particle(inout ParticleData particle_data, float random_seed)
{
    float t1 = rand(vec2(TIME, random_seed));
    float t2 = rand(vec2(TIME, t1 + PI));
    float t3 = rand(vec2(TIME, t2 + PI));
    float t4 = rand(vec2(TIME, t3 + PI));
    float t5 = rand(vec2(TIME, t4 + PI));
    float t6 = rand(vec2(TIME, t5 + PI));
    float t7 = rand(vec2(TIME, t6 + PI));
    float t8 = rand(vec2(TIME, t7 + PI));
    float t9 = rand(vec2(TIME, t8 + PI));
    float t10 = rand(vec2(TIME, t9 + PI));
    float t11 = rand(vec2(TIME, t10 + PI));
    float t12 = rand(vec2(TIME, t11 + PI));
    float t13 = rand(vec2(TIME, t12 + PI));
    float t14 = rand(vec2(TIME, t13 + PI));
    float t15 = rand(vec2(TIME, t14 + PI));
    float t16 = rand(vec2(TIME, t15 + PI));
    float t17 = rand(vec2(TIME, t16 + PI));
    float t18 = rand(vec2(TIME, t17 + PI));
    float t19 = rand(vec2(TIME, t18 + PI));
    float t20 = rand(vec2(TIME, t19 + PI));

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
    if(gl_GlobalInvocationID.x < PARTICLE_SPAWN_COUNT)
    {
        uint index = min(PARTICLE_MAX_COUNT, alive_particle_counter + gl_GlobalInvocationID.x);
        uint id = alive_particle_index[index];
        spawn_particle(particle_datas[id], float(id) + PI);
    }
}
#endif
