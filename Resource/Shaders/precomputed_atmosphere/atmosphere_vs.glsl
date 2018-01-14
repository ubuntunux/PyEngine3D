#include "scene_constants.glsl"

uniform mat4 model_from_view;
uniform mat4 view_from_clip;

#ifdef GL_VERTEX_SHADER
layout(location = 0) in vec4 vertex;
out vec3 view_ray;
out vec2 uv;
void main()
{
    uv = vertex.xy * 0.5 + 0.5;
    view_ray = (model_from_view * vec4((view_from_clip * vertex).xyz, 0.0)).xyz;
    gl_Position = vertex;
}
#endif