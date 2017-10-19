#version 430 core

//----------- UNIFORM_BLOCK ---------------//

#include "scene_constants.glsl"

uniform mat4 model;
uniform mat4 view_projection;
uniform vec4 diffuseColor;

//----------- INPUT and OUTPUT ---------------//

struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 texcoord;
};

//----------- VERTEX_SHADER ---------------//

#ifdef VERTEX_SHADER
in VERTEX_INPUT vs_input;

void main() {
    gl_Position = PERSPECTIVE * VIEW * model * vec4(vs_input.position, 1.0);
}
#endif // VERTEX_SHADER

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
out vec4 fs_output;

void main() {
    fs_output = vec4(1.0, 1.0, 0.0, 1.0);
}
#endif // FRAGMENT_SHADER