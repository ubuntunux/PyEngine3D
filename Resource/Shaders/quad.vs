#version 430 core

layout(location=0) vec3 position;

void main() {
    gl_Position = vec4(vertex.position, 1.0);
}