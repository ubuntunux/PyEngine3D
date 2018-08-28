#include "scene_constants.glsl"
#include "utility.glsl"


uniform bool enable_force_field;
uniform sampler3D texture_force_field;
uniform float force_field_strength;
uniform vec3 force_field_offset;
uniform vec3 force_field_radius;


#ifdef GL_COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer emitter_buffer { EmitterData emitter_datas[]; };
layout( binding=1 ) uniform atomic_uint emitter_counter;

void refresh(uint id)
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

    emitter_datas[id].delay = mix(EMITTER_DELAY.x, EMITTER_DELAY.y, t1);
    emitter_datas[id].state = (0.0 < emitter_datas[id].delay) ? EMITTER_STATE_DELAY : EMITTER_STATE_ALIVE;
    emitter_datas[id].life_time = mix(EMITTER_LIFE_TIME.x, EMITTER_LIFE_TIME.y, t2);
    emitter_datas[id].transform_position = mix(EMITTER_TRANSFORM_POSITION_MIN, EMITTER_TRANSFORM_POSITION_MAX, vec3(t3, t4, t5));
    emitter_datas[id].transform_rotation = mix(EMITTER_TRANSFORM_ROTATION_MIN, EMITTER_TRANSFORM_ROTATION_MAX, vec3(t9, t10, t11));
    emitter_datas[id].transform_scale = mix(EMITTER_TRANSFORM_SCALE_MIN, EMITTER_TRANSFORM_SCALE_MAX, vec3(t15, t16, t17));
    emitter_datas[id].velocity_position = mix(EMITTER_VELOCITY_POSITION_MIN, EMITTER_VELOCITY_POSITION_MAX, vec3(t6, t7, t8));
    emitter_datas[id].velocity_rotation = mix(EMITTER_VELOCITY_ROTATION_MIN, EMITTER_VELOCITY_ROTATION_MAX, vec3(t12, t13, t14));
    emitter_datas[id].velocity_scale = mix(EMITTER_VELOCITY_SCALE_MIN, EMITTER_VELOCITY_SCALE_MAX, vec3(t18, t19, t20));
    emitter_datas[id].opacity = EMITTER_OPACITY;
    emitter_datas[id].parent_matrix = EMITTER_PARENT_MATRIX;
    // We will apply inverse_matrix here because we will apply parent_matrix later.
    emitter_datas[id].force = (EMITTER_PARENT_INVERSE_MATRIX * vec4(0.0, -EMITTER_FORCE_GRAVITY, 0.0, 1.0)).xyz;
    emitter_datas[id].local_matrix = mat4(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0);
}


void update_sequence(uint id, float life_ratio)
{
    const int emitter_total_cell_count = EMITTER_CELL_COUNT[0] * EMITTER_CELL_COUNT[1];

    if(1 < emitter_total_cell_count && 0.0 < EMITTER_PLAY_SPEED)
    {
        float ratio = life_ratio * EMITTER_PLAY_SPEED;
        ratio = float(emitter_total_cell_count - 1) * (ratio - floor(ratio));

        int index = clamp(int(floor(ratio)), 0, emitter_total_cell_count - 1);
        int next_index = (index == (emitter_total_cell_count - 1)) ? 0 : index + 1;

        emitter_datas[id].sequence_ratio = ratio - float(index);

        if(next_index == emitter_datas[id].next_sequence_index)
        {
            return;
        }

        emitter_datas[id].sequence_index = emitter_datas[id].next_sequence_index;
        emitter_datas[id].sequence_uv = emitter_datas[id].next_sequence_uv;
        emitter_datas[id].next_sequence_index = next_index;
        emitter_datas[id].next_sequence_uv.x = mod(next_index, EMITTER_CELL_COUNT.x) / float(EMITTER_CELL_COUNT.x);
        emitter_datas[id].next_sequence_uv.y = float(EMITTER_CELL_COUNT.y - 1 - int(floor(next_index / EMITTER_CELL_COUNT.x))) / float(EMITTER_CELL_COUNT.y);
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
        emitter_datas[id].transform_scale.x, 0.0, 0.0, 0.0,
        0.0, emitter_datas[id].transform_scale.y, 0.0, 0.0,
        0.0, 0.0, emitter_datas[id].transform_scale.z, 0.0,
        0.0, 0.0, 0.0, 1.0);

    float ch = 1.0;
    float sh = 0.0;
    float ca = 1.0;
    float sa = 0.0;
    float cb = 1.0;
    float sb = 0.0;
    bool has_rotation = false;

    if(0.0 != emitter_datas[id].transform_rotation.x)
    {
        cb = cos(emitter_datas[id].transform_rotation.x);
        sb = sin(emitter_datas[id].transform_rotation.x);
        has_rotation = true;
    }

    if(0.0 != emitter_datas[id].transform_rotation.y)
    {
        ch = cos(emitter_datas[id].transform_rotation.y);
        sh = sin(emitter_datas[id].transform_rotation.y);
        has_rotation = true;
    }

    if(0.0 != emitter_datas[id].transform_rotation.z)
    {
        ca = cos(emitter_datas[id].transform_rotation.z);
        sa = sin(emitter_datas[id].transform_rotation.z);
        has_rotation = true;
    }

    if(has_rotation)
    {
        rotation_matrix[0] = vec4(ch*ca, sa, -sh*ca, 0.0);
        rotation_matrix[1] = vec4(sh*sb - ch*sa*cb, ca*cb, sh*sa*cb + ch*sb, 0.0);
        rotation_matrix[2] = vec4(ch*sa*sb + sh*cb, -ca*sb, -sh*sa*sb + ch*cb, 0.0);
    }

    emitter_datas[id].local_matrix = rotation_matrix * scale_matrix;
    emitter_datas[id].local_matrix[3].xyz = emitter_datas[id].transform_position.xyz;
}


void main()
{
    uint particle_count = atomicCounterIncrement( emitter_counter );
    uint id = gl_GlobalInvocationID.x;

    if(EMITTER_STATE_DEAD == emitter_datas[id].state)
    {
        return;
    }

    if(EMITTER_STATE_NONE == emitter_datas[id].state)
    {
        refresh(id);

        emitter_datas[id].loop_remain = EMITTER_LOOP;
        emitter_datas[id].elapsed_time = 0.0;
        emitter_datas[id].sequence_ratio = 0.0;
        emitter_datas[id].sequence_index = 0;
        emitter_datas[id].next_sequence_index = 0;
    }

    if(EMITTER_STATE_DELAY == emitter_datas[id].state)
    {
        emitter_datas[id].delay -= DELTA_TIME;
        if(0.0 < emitter_datas[id].delay)
        {
            return;
        }
        emitter_datas[id].delay = 0.0;
        emitter_datas[id].state = EMITTER_STATE_ALIVE;
    }

    if(EMITTER_STATE_ALIVE == emitter_datas[id].state)
    {
        emitter_datas[id].elapsed_time += DELTA_TIME;

        if(emitter_datas[id].life_time < emitter_datas[id].elapsed_time)
        {
            emitter_datas[id].elapsed_time = mod(emitter_datas[id].elapsed_time, emitter_datas[id].life_time);

            if(0 < emitter_datas[id].loop_remain)
            {
                emitter_datas[id].loop_remain -= 1;
            }

            if(0 == emitter_datas[id].loop_remain)
            {
                emitter_datas[id].state = EMITTER_STATE_DEAD;
                return;
            }

            refresh(id);
        }

        float life_ratio = 0.0;
        float elapsed_time = emitter_datas[id].elapsed_time;
        float life_time = emitter_datas[id].life_time;

        if(0.0 < emitter_datas[id].life_time)
        {
            life_ratio = clamp(elapsed_time / emitter_datas[id].life_time, 0.0, 1.0);
        }

        update_sequence(id, life_ratio);

        emitter_datas[id].velocity_position += emitter_datas[id].force * DELTA_TIME;

        if(enable_force_field)
        {
            vec3 uvw = force_field_offset + emitter_datas[id].transform_position / force_field_radius;
            uvw = (EMITTER_PARENT_MATRIX * vec4(uvw, 0.0)).xyz;
            vec3 force = texture3D(texture_force_field, uvw - vec3(0.5)).xyz;
            emitter_datas[id].velocity_position += force * force_field_strength * DELTA_TIME;
        }

        emitter_datas[id].transform_position += emitter_datas[id].velocity_position * DELTA_TIME;
        emitter_datas[id].transform_rotation += emitter_datas[id].velocity_rotation * DELTA_TIME;
        emitter_datas[id].transform_scale += emitter_datas[id].velocity_scale * DELTA_TIME;

        // update transform
        update_local_matrix(id);

        // update opacity
        emitter_datas[id].opacity = EMITTER_OPACITY;

        float left_elapsed_time = life_time - elapsed_time;

        if(0.0 < EMITTER_FADE_IN && elapsed_time < EMITTER_FADE_IN)
        {
            emitter_datas[id].opacity *= elapsed_time / EMITTER_FADE_IN;
        }

        if(0.0 < EMITTER_FADE_OUT && left_elapsed_time < EMITTER_FADE_OUT)
        {
            emitter_datas[id].opacity *= left_elapsed_time / EMITTER_FADE_OUT;
        }
    }
}
#endif
