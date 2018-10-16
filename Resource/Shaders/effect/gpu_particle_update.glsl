#include "scene_constants.glsl"
#include "utility.glsl"


uniform bool enable_vector_field;
uniform sampler3D texture_vector_field;
uniform float vector_field_strength;
uniform vec3 vector_field_offset;
uniform vec3 vector_field_radius;


#ifdef COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer particle_buffer { ParticleData particle_datas[]; };
layout( binding=1 ) uniform atomic_uint particle_counter;

void spawn_particle(uint id)
{
    // initialize
    float t1 = rand(vec2(TIME, float(id) + PI));
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

    particle_datas[id].delay = mix(PARTICLE_DELAY.x, PARTICLE_DELAY.y, t1);
    particle_datas[id].state = (0.0 < particle_datas[id].delay) ? PARTICLE_STATE_DELAY : PARTICLE_STATE_ALIVE;
    particle_datas[id].life_time = mix(PARTICLE_LIFE_TIME.x, PARTICLE_LIFE_TIME.y, t2);
    particle_datas[id].transform_position = mix(PARTICLE_TRANSFORM_POSITION_MIN, PARTICLE_TRANSFORM_POSITION_MAX, vec3(t3, t4, t5));
    particle_datas[id].transform_rotation = mix(PARTICLE_TRANSFORM_ROTATION_MIN, PARTICLE_TRANSFORM_ROTATION_MAX, vec3(t9, t10, t11));
    particle_datas[id].transform_scale = mix(PARTICLE_TRANSFORM_SCALE_MIN, PARTICLE_TRANSFORM_SCALE_MAX, vec3(t15, t16, t17));
    particle_datas[id].velocity_position = mix(PARTICLE_VELOCITY_POSITION_MIN, PARTICLE_VELOCITY_POSITION_MAX, vec3(t6, t7, t8));
    particle_datas[id].velocity_rotation = mix(PARTICLE_VELOCITY_ROTATION_MIN, PARTICLE_VELOCITY_ROTATION_MAX, vec3(t12, t13, t14));
    particle_datas[id].velocity_scale = mix(PARTICLE_VELOCITY_SCALE_MIN, PARTICLE_VELOCITY_SCALE_MAX, vec3(t18, t19, t20));
    particle_datas[id].opacity = PARTICLE_OPACITY;
    particle_datas[id].parent_matrix = PARTICLE_PARENT_MATRIX;
    // We will apply inverse_matrix here because we will apply parent_matrix later.
    particle_datas[id].force = (PARTICLE_PARENT_INVERSE_MATRIX * vec4(0.0, -PARTICLE_FORCE_GRAVITY, 0.0, 1.0)).xyz;
    particle_datas[id].local_matrix = mat4(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0);

    particle_datas[id].elapsed_time = 0.0;
    particle_datas[id].sequence_ratio = 0.0;
    particle_datas[id].sequence_index = 0;
    particle_datas[id].next_sequence_index = 0;
}


void update_sequence(uint id, float life_ratio)
{
    const int particle_total_cell_count = PARTICLE_CELL_COUNT[0] * PARTICLE_CELL_COUNT[1];

    if(1 < particle_total_cell_count && 0.0 < PARTICLE_PLAY_SPEED)
    {
        float ratio = life_ratio * PARTICLE_PLAY_SPEED;
        ratio = float(particle_total_cell_count - 1) * (ratio - floor(ratio));

        int index = int(ratio);
        int next_index = min(index + 1, particle_total_cell_count - 1);

        particle_datas[id].sequence_ratio = ratio - float(index);

        if(next_index == particle_datas[id].next_sequence_index)
        {
            return;
        }

        particle_datas[id].sequence_index = particle_datas[id].next_sequence_index;
        particle_datas[id].sequence_uv = particle_datas[id].next_sequence_uv;
        particle_datas[id].next_sequence_index = next_index;
        particle_datas[id].next_sequence_uv.x = mod(next_index, PARTICLE_CELL_COUNT.x) / float(PARTICLE_CELL_COUNT.x);
        particle_datas[id].next_sequence_uv.y = float(PARTICLE_CELL_COUNT.y - 1 - int(floor(next_index / PARTICLE_CELL_COUNT.x))) / float(PARTICLE_CELL_COUNT.y);
    }
}


void update_local_matrix(uint id)
{
    mat4 rotation_matrix = mat4(
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0);

    mat4 scale_matrix = mat4(
        particle_datas[id].transform_scale.x, 0.0, 0.0, 0.0,
        0.0, particle_datas[id].transform_scale.y, 0.0, 0.0,
        0.0, 0.0, particle_datas[id].transform_scale.z, 0.0,
        0.0, 0.0, 0.0, 1.0);

    float ch = 1.0;
    float sh = 0.0;
    float ca = 1.0;
    float sa = 0.0;
    float cb = 1.0;
    float sb = 0.0;
    bool has_rotation = false;

    if(0.0 != particle_datas[id].transform_rotation.x)
    {
        cb = cos(particle_datas[id].transform_rotation.x);
        sb = sin(particle_datas[id].transform_rotation.x);
        has_rotation = true;
    }

    if(0.0 != particle_datas[id].transform_rotation.y)
    {
        ch = cos(particle_datas[id].transform_rotation.y);
        sh = sin(particle_datas[id].transform_rotation.y);
        has_rotation = true;
    }

    if(0.0 != particle_datas[id].transform_rotation.z)
    {
        ca = cos(particle_datas[id].transform_rotation.z);
        sa = sin(particle_datas[id].transform_rotation.z);
        has_rotation = true;
    }

    if(has_rotation)
    {
        rotation_matrix[0] = vec4(ch*ca, sa, -sh*ca, 0.0);
        rotation_matrix[1] = vec4(sh*sb - ch*sa*cb, ca*cb, sh*sa*cb + ch*sb, 0.0);
        rotation_matrix[2] = vec4(ch*sa*sb + sh*cb, -ca*sb, -sh*sa*sb + ch*cb, 0.0);
        particle_datas[id].local_matrix = rotation_matrix * scale_matrix;
    }
    else
    {
        particle_datas[id].local_matrix = scale_matrix;
    }

    
    particle_datas[id].local_matrix[3].xyz = particle_datas[id].transform_position.xyz;
}


void main()
{
    uint id = gl_GlobalInvocationID.x;

    if(PARTICLE_STATE_DEAD == particle_datas[id].state)
    {
        return;
    }

    if(PARTICLE_STATE_NONE == particle_datas[id].state)
    {
        spawn_particle(id);
    }

    if(PARTICLE_STATE_DELAY == particle_datas[id].state)
    {
        particle_datas[id].delay -= DELTA_TIME;
        if(0.0 < particle_datas[id].delay)
        {
            particle_datas[id].elapsed_time = abs(particle_datas[id].delay);
            particle_datas[id].delay = 0.0;
            particle_datas[id].state = PARTICLE_STATE_ALIVE;
        }
        else
        {
            return;
        }
    }

    if(PARTICLE_STATE_ALIVE == particle_datas[id].state)
    {
        particle_datas[id].elapsed_time += DELTA_TIME;

        if(particle_datas[id].life_time < particle_datas[id].elapsed_time)
        {
            // for respawn
            particle_datas[id].state = PARTICLE_STATE_NONE;
            //particle_datas[id].state = PARTICLE_STATE_DEAD;
            return;
        }

        float life_ratio = 0.0;
        float elapsed_time = particle_datas[id].elapsed_time;
        float life_time = particle_datas[id].life_time;

        if(0.0 < particle_datas[id].life_time)
        {
            life_ratio = clamp(elapsed_time / particle_datas[id].life_time, 0.0, 1.0);
        }

        update_sequence(id, life_ratio);

        particle_datas[id].velocity_position += particle_datas[id].force * DELTA_TIME;

        if(PARTICLE_ENABLE_VECTOR_FIELD)
        {
            vec3 uvw = (PARTICLE_VECTOR_FIELD_INV_MATRIX * vec4(particle_datas[id].transform_position, 1.0)).xyz;
            vec3 force = texture3D(texture_vector_field, uvw - vec3(0.5)).xyz;
            force = (PARTICLE_VECTOR_FIELD_MATRIX * vec4(force, 1.0)).xyz;
            particle_datas[id].velocity_position = mix(particle_datas[id].velocity_position, force, PARTICLE_VECTOR_FIELD_TIGHTNESS);
            particle_datas[id].velocity_position += force * PARTICLE_VECTOR_FIELD_STRENGTH * DELTA_TIME;
        }

        particle_datas[id].transform_position += particle_datas[id].velocity_position * DELTA_TIME;
        particle_datas[id].transform_rotation += particle_datas[id].velocity_rotation * DELTA_TIME;
        particle_datas[id].transform_scale += particle_datas[id].velocity_scale * DELTA_TIME;

        // update transform
        update_local_matrix(id);

        // update opacity
        particle_datas[id].opacity = PARTICLE_OPACITY;

        float left_elapsed_time = life_time - elapsed_time;

        if(0.0 < PARTICLE_FADE_IN && elapsed_time < PARTICLE_FADE_IN)
        {
            particle_datas[id].opacity *= elapsed_time / PARTICLE_FADE_IN;
        }

        if(0.0 < PARTICLE_FADE_OUT && left_elapsed_time < PARTICLE_FADE_OUT)
        {
            particle_datas[id].opacity *= left_elapsed_time / PARTICLE_FADE_OUT;
        }
    }
}
#endif
