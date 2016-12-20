#version 330 core

attribute vec3 position;

layout(std140) uniform pvMatrix
{
    mat4 view;
    mat4 perspective;
};

uniform mat4 model;

void main() {
    gl_Position = perspective * view * model * vec4(position, 1.0f);
}