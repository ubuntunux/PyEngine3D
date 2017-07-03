#version 430 core

#define SKELETAL 0

//----------- UNIFORM_BLOCK ---------------//

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
uniform mat4 mat1;
uniform mat4 mat2;


//----------- INPUT and OUTPUT ---------------//

struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 texcoord;
#if SKELETAL
    layout(location=5) vec4 bone_indicies;
    layout(location=6) vec4 bone_weights;
#endif
};

struct VERTEX_OUTPUT
{
    vec3 worldPosition;
    vec4 vertexColor;
    vec3 normalVector;
    mat4 tangentToWorld;
    vec2 texCoord;
    vec3 cameraVector;
    vec3 lightVector;
#if SKELETAL
    vec4 bone_indicies;
    vec4 bone_weights;
#endif
};

//----------- VERTEX_SHADER ---------------//

#ifdef VERTEX_SHADER
in VERTEX_INPUT vs_input;
out VERTEX_OUTPUT vs_output;

void main() {
    vs_output.vertexColor = vs_input.color;

    vec3 local_pos = vs_input.position.xyz * vec3(0.1, 1.0, 0.1);

    if(vs_input.position.y > 10.0)
    {
        vs_output.worldPosition = (model * vec4(local_pos, 1.0)).xyz;
    }
    else if(vs_input.position.y > 0.0)
    {
        vs_output.worldPosition = (mat2 * vec4(local_pos, 1.0)).xyz;
    }
    else
    {
        vs_output.worldPosition = (mat1 * vec4(local_pos, 1.0)).xyz;
    }

    vs_output.normalVector = (model * vec4(vs_input.normal, 0.0)).xyz;
    vec3 bitangent = cross(vs_input.tangent, vs_input.normal);
    vs_output.tangentToWorld = model * mat4(vec4(vs_input.tangent, 0.0), vec4(bitangent, 0.0), vec4(vs_input.normal, 0.0),
        vec4(0.0, 0.0, 0.0, 1.0));
    vs_output.texCoord = vs_input.texcoord;


#if SKELETAL
    vs_output.bone_indicies = vs_input.bone_indicies;
    vs_output.bone_weights = vs_input.bone_weights;
#endif

    vs_output.cameraVector = cameraPosition.xyz - vs_output.worldPosition;
    vs_output.lightVector = lightPosition.xyz - vs_output.worldPosition;

    if(vs_input.position.y > 10.0)
    {
        gl_Position = mvp * vec4(vs_input.position, 1.0f);
    }
    else
    {
        gl_Position = perspective * view * vec4(vs_output.worldPosition.xyz, 1.0);
    }
}
#endif

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    fs_output = vec4(1.0, 1.0, 1.0, 1.0);
}
#endif