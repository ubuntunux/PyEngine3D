#ifdef GL_COMPUTE_SHADER
layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(std430, binding=0) buffer InputPos { vec3 pos[]; };

uniform float time;

void main()
{
    pos[gl_GlobalInvocationID.x] = vec3(gl_GlobalInvocationID.x + time);
}
#endif