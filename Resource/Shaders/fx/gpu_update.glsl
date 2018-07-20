#include "scene_constants.glsl"


#ifdef GL_COMPUTE_SHADER
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;

layout(std430, binding=0) buffer emitter_buffer { EmitterData emitter_datas[]; };

void main()
{
    float t = fract(TIME * float(gl_GlobalInvocationID.x));
    uint id = gl_GlobalInvocationID.x;

    /*if(emitter_datas[id].alive)
    {
        //emitter_datas[id].velocity += vec3(0.0, -emitter_datas[id].gravity, 0.0) * 0.1;
        //emitter_datas[id].position += emitter_datas[id].velocity * 0.1;
    }
    else
    {
        emitter_datas[id].alive = true;
        emitter_datas[id].velocity = mix(emitter_velocity_min, emitter_velocity_max, t);
    }*/

    emitter_datas[id].position.xyz = vec3(id);
}
#endif