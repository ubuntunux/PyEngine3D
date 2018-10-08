#include "scene_constants.glsl"

#ifdef VERTEX_SHADER
layout(location = 0) in vec4 vertex;
out vec2 uv;
void main()
{
    uv = vertex.xy * 0.5 + 0.5;
    gl_Position = vertex;
}
#endif