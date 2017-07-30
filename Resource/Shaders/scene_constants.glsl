#version 430 core

layout(std140, binding=0) uniform sceneConstants
{
    mat4 view;
    mat4 perspective;
    vec4 cameraPosition;
    vec4 near_far;
};

layout(std140, binding=1) uniform lightConstants
{
    vec4 lightPosition;
    vec4 lightDir;
    vec4 lightColor;
};

const int MAX_BONES_PER_VERTEX = 4;
const int MAX_BONES = 72;
const float shadow_bias = 0.00000005;