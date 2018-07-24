#include "scene_constants.glsl"
#include "utility.glsl"


#ifdef GL_COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer emitter_buffer { EmitterData emitter_datas[]; };

void refresh(uint id)
{
    // initialize
    float r1 = rand(vec2(TIME, float(id) + PI));
    float r2 = rand(vec2(TIME, r1 + PI));
    float r3 = rand(vec2(TIME, r2 + PI));
    float r4 = rand(vec2(TIME, r3 + PI));
    float r5 = rand(vec2(TIME, r4 + PI));
    float r6 = rand(vec2(TIME, r5 + PI));
    float r7 = rand(vec2(TIME, r6 + PI));
    float r8 = rand(vec2(TIME, r7 + PI));

    emitter_datas[id].state = EMITTER_STATE_ALIVE;
    emitter_datas[id].delay = mix(EMITTER_DELAY.x, EMITTER_DELAY.y, r1);
    emitter_datas[id].life_time = mix(EMITTER_LIFE_TIME.x, EMITTER_LIFE_TIME.y, r2);
    emitter_datas[id].position = mix(EMITTER_POSITION_MIN, EMITTER_POSITION_MAX, vec3(r3, r4, r5));
    emitter_datas[id].velocity = mix(EMITTER_VELOCITY_MIN, EMITTER_VELOCITY_MAX, vec3(r6, r7, r8));

    emitter_datas[id].loop_remain = EMITTER_LOOP;
    emitter_datas[id].elapsed_time = 0.0;
    emitter_datas[id].sequence_ratio = 0.0;
    emitter_datas[id].sequence_index = 0;
    emitter_datas[id].next_sequence_index = 0;
}


void update_sequence(uint id, float life_ratio)
{
    if(1 < EMITTER_TOTAL_CELL_COUNT && 0 < EMITTER_PLAY_SPEED)
    {
        float ratio = life_ratio * EMITTER_PLAY_SPEED;
        ratio = float(EMITTER_TOTAL_CELL_COUNT) * (ratio - floor(ratio));
        int index = int(floor(ratio));
        int next_index = int(mod(index + 1, EMITTER_TOTAL_CELL_COUNT));
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


void main()
{
    uint id = gl_GlobalInvocationID.x;

    if(EMITTER_STATE_DEAD == emitter_datas[id].state)
    {
        return;
    }

    if(0.0 < emitter_datas[id].delay)
    {
        emitter_datas[id].delay -= DELTA_TIME;
        if(0.0 < emitter_datas[id].delay)
        {
            return;
        }
        emitter_datas[id].delay = 0.0;
    }

    if(EMITTER_STATE_NONE == emitter_datas[id].state)
    {
        refresh(id);
    }
    else
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
        if(0.0 < emitter_datas[id].life_time)
        {
            life_ratio = emitter_datas[id].elapsed_time / emitter_datas[id].life_time;
        }

        update_sequence(id, life_ratio);

        emitter_datas[id].velocity += vec3(0.0, -EMITTER_GRAVITY, 0.0) * DELTA_TIME;
        emitter_datas[id].position += emitter_datas[id].velocity * DELTA_TIME;
        emitter_datas[id].life_time -= DELTA_TIME;
        emitter_datas[id].opacity = 1.0;
    }
}
#endif