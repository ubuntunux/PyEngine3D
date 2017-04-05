#version 430 core

in struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 texcoord;
} vertex;

layout(std140, binding=0) uniform sceneConstants
{
    mat4 view;
    mat4 perspective;
    vec4 cameraPosition;
};

layout(std140, binding=1) uniform lightConstants
{
    vec4 lightPosition;
    vec4 lightColor;
};

uniform mat4 model;
uniform mat4 mvp;

out struct DATA
{
    vec3 worldPosition;
    vec4 vertexColor;
    vec3 normalVector;
    mat4 tangentToWorld;
    vec2 texCoord;
    vec3 cameraVector;
    vec3 lightVector;
} data;

void main() {
    data.vertexColor = vertex.color;
    data.worldPosition = (model * vec4(vertex.position, 1.0)).xyz;
    data.normalVector = (model * vec4(vertex.normal, 0.0)).xyz;
    vec3 bitangent = cross(vertex.tangent, vertex.normal);
    data.tangentToWorld = model * mat4(vec4(vertex.tangent, 0.0), vec4(bitangent, 0.0), vec4(vertex.normal, 0.0),
        vec4(0.0, 0.0, 0.0, 1.0));
    data.texCoord = vertex.texcoord;

    data.cameraVector = cameraPosition.xyz - data.worldPosition;
    //data.cameraVector = normalize(data.cameraVector);

    data.lightVector = lightPosition.xyz - data.worldPosition;
    //data.lightVector = normalize(data.lightVector);
    gl_Position = mvp * vec4(vertex.position, 1.0f);
}