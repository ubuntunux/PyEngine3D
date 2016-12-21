#version 330 core

attribute vec3 position;
attribute vec4 color;
attribute vec3 normal;
attribute vec3 tangent;
attribute vec2 texcoord;

layout(std140) uniform commonConstants
{
    mat4 view;
    mat4 perspective;
    vec3 camera_position;
};

uniform mat4 model;
uniform mat4 mvp;
uniform vec3 light_position;

struct DATA
{
    vec3 worldPosition;
    vec4 vertexColor;
    vec3 normalVector;
    mat4 tangentToWorld;
    vec2 textureCoordinate;
    vec3 cameraVector;
    vec3 cameraPosition;
    vec3 lightVector;
    vec3 lightPosition;
};

out DATA data;

void main() {
    data.vertexColor = color;
    data.worldPosition = (model * vec4(position, 1.0)).xyz;
    data.normalVector = (model * vec4(normal, 0.0)).xyz;
    vec3 bitangent = cross(tangent, normal);
    data.tangentToWorld = mat4(model * vec4(tangent, 0.0), model * vec4(bitangent,0.0), model * vec4(normal, 0.0), model * vec4(0.0, 0.0, 0.0, 1.0));
    data.textureCoordinate = texcoord;

    data.cameraPosition = camera_position;
    data.cameraVector = camera_position - data.worldPosition;
    //data.cameraVector = normalize(data.cameraVector);

    data.lightPosition = light_position;
    data.lightVector = light_position - data.worldPosition;
    //data.lightVector = normalize(data.lightVector);
    gl_Position = mvp * vec4(position, 1.0f);
}