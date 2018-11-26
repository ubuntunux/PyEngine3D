#include "quad.glsl"

uniform vec3 color;

#ifdef FRAGMENT_SHADER
layout(location=0) out vec4 fs_output;

void main(void)
{
    fs_output.xyz = color;
    fs_output.w = 1.0;
}
#endif