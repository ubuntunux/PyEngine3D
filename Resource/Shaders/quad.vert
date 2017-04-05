#version 430 core

in struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 texcoord;
} vs_input;

out struct VERTEX_OUTPUT
{
    vec2 texcoord;
    vec3 position;
} vs_output;

void main() {
    vs_output.texcoord = vs_input.texcoord;
    vs_output.position = vs_input.position;
    gl_Position = vec4(vs_input.position, 1.0);
}