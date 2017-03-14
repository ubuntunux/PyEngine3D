#version 430 core

in struct VERTEX_ARRAY
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 texcoord;
} vertex;

layout(std140) uniform sceneConstants
{
    mat4 view;
    mat4 perspective;
    vec4 cameraPosition;
};

layout(std140) uniform lightConstants
{
    vec4 lightPosition;
    vec4 lightColor;
};

uniform mat4 model;
uniform mat4 mvp;

void main() {
    gl_Position = perspective * view * model * vec4(vertex.position, 1.0);
}