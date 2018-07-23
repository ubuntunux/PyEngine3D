#include "scene_constants.glsl"


#ifdef GL_COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer emitter_buffer { EmitterData emitter_datas[]; };

void main()
{
    uint id = gl_GlobalInvocationID.x;

    if(0 == emitter_datas[id].alive || emitter_datas[id].life_time <= 0.0)
    {
        float r1 = fract(TIME * float(gl_GlobalInvocationID.x) + 3.141592);
        float r2 = fract(TIME * r1 + 3.141592);
        float r3 = fract(TIME * r2 + 3.141592);

        emitter_datas[id].alive = 1;
        emitter_datas[id].life_time = r1;
        emitter_datas[id].position = vec3(0.0, 2.0, 0.0);
        emitter_datas[id].velocity = mix(emitter_velocity_min, emitter_velocity_max, vec3(r1, r2, r3));
    }
    else
    {
        emitter_datas[id].velocity += vec3(0.0, -emitter_datas[id].gravity, 0.0) * DELTA_TIME;
        emitter_datas[id].position += emitter_datas[id].velocity * DELTA_TIME;
        emitter_datas[id].life_time -= DELTA_TIME;
    }
}
#endif