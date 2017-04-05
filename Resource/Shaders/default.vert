#version 430 core
#version 440 core

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

struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 texcoord;
};

struct VERTEX_OUT
{
    vec3 worldPosition;
    vec4 vertexColor;
    vec3 normalVector;
    mat4 tangentToWorld;
    vec2 texCoord;
    vec3 cameraVector;
    vec3 lightVector;
};

#ifdef VERTEX_SHADER
in VERTEX_INPUT vs_input;
out VERTEX_OUT vs_output;

void main() {
    vs_output.vertexColor = vs_input.color;
    vs_output.worldPosition = (model * vec4(vs_input.position, 1.0)).xyz;
    vs_output.normalVector = (model * vec4(vs_input.normal, 0.0)).xyz;
    vec3 bitangent = cross(vs_input.tangent, vs_input.normal);
    vs_output.tangentToWorld = model * mat4(vec4(vs_input.tangent, 0.0), vec4(bitangent, 0.0), vec4(vs_input.normal, 0.0),
        vec4(0.0, 0.0, 0.0, 1.0));
    vs_output.texCoord = vs_input.texcoord;

    vs_output.cameraVector = cameraPosition.xyz - vs_output.worldPosition;
    //vs_output.cameraVector = normalize(vs_output.cameraVector);

    vs_output.lightVector = lightPosition.xyz - vs_output.worldPosition;
    //vs_output.lightVector = normalize(vs_output.lightVector);
    gl_Position = mvp * vec4(vs_input.position, 1.0f);
}
#endif