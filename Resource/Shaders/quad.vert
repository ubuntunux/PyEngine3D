#version 430 core

in struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 texcoord;
} vertex;

out struct DATA
{
    vec2 texcoord;
    vec3 position;
} data;

void main() {
    data.texcoord = vertex.texcoord;
    data.position = vertex.position;
    gl_Position = vec4(vertex.position, 1.0);
}