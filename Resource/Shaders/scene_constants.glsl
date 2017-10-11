#version 430 core

layout(std140, binding=0) uniform sceneConstants
{
    float time;
};

layout(std140, binding=1) uniform viewConstants
{
    mat4 view;
    mat4 inv_view;
    mat4 view_origin;
    mat4 inv_view_origin;
    mat4 perspective;
    mat4 inv_perspective;
    vec4 camera_position;
    vec4 near_far;
};

layout(std140, binding=2) uniform viewProjection
{
    mat4 view_projection;
    mat4 prev_view_projection;
};

layout(std140, binding=3) uniform lightConstants
{
    vec4 lightPosition;
    vec4 lightDir;
    vec4 lightColor;
    mat4 shadow_matrix;
};

const int MAX_BONES_PER_VERTEX = 4;
const int MAX_BONES = 100;
const float shadow_bias = -0.0001;