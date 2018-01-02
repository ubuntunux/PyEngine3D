#include "scene_constants.glsl"

#ifdef GL_VERTEX_SHADER
layout(location = 0) in vec2 vertex;
void main() {
    gl_Position = vec4(vertex, 0.0, 1.0);
}
#endif