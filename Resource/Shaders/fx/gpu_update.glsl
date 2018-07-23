#include "scene_constants.glsl"
#include "utility.glsl"


#ifdef GL_COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer emitter_buffer { EmitterData emitter_datas[]; };

void main()
{
    uint id = gl_GlobalInvocationID.x;

    if(0 == emitter_datas[id].alive || emitter_datas[id].life_time <= 0.0)
    {
        // initialize
        float r1 = rand(vec2(TIME, float(id) + PI));
        float r2 = rand(vec2(TIME, r1 + PI));
        float r3 = rand(vec2(TIME, r2 + PI));
        float r4 = rand(vec2(TIME, r3 + PI));
        float r5 = rand(vec2(TIME, r4 + PI));
        float r6 = rand(vec2(TIME, r5 + PI));
        float r7 = rand(vec2(TIME, r6 + PI));

        emitter_datas[id].alive = 1;
        emitter_datas[id].life_time = mix(emitter_life_time.x, emitter_life_time.y, r1);
        emitter_datas[id].position = mix(emitter_position_min, emitter_position_max, vec3(r2, r3, r4));
        emitter_datas[id].velocity = mix(emitter_velocity_min, emitter_velocity_max, vec3(r5, r6, r7));
    }
    else
    {
        // update
        emitter_datas[id].velocity += vec3(0.0, -emitter_gravity, 0.0) * DELTA_TIME;
        emitter_datas[id].position += emitter_datas[id].velocity * DELTA_TIME;
        emitter_datas[id].life_time -= DELTA_TIME;
    }
}
#endif