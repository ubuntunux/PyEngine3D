#version 430 core

#define SKELETAL 0

#include "scene_constants.glsl"

//----------- UNIFORM_BLOCK ---------------//

#if 1 == SKELETAL
uniform mat4 bone_matrices[MAX_BONES];
uniform mat4 prev_bone_matrices[MAX_BONES];
#endif

uniform mat4 model;
uniform mat4 view_projection;
uniform mat4 prev_view_projection;

//-------------- MATERIAL_COMPONENTS ---------------//

#include "default_material.glsl"

//----------- INPUT and OUTPUT ---------------//

struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 texcoord;
#if 1 == SKELETAL
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
    float cameraDistance;
    vec3 lightVector;
    float lightDistance;
    vec2 velocity;
};

//----------- VERTEX_SHADER ---------------//

#ifdef VERTEX_SHADER
in VERTEX_INPUT vs_input;
out VERTEX_OUTPUT vs_output;

void main() {
    vec4 position = vec4(0.0, 0.0, 0.0, 0.0);
    vec4 prev_position = vec4(0.0, 0.0, 0.0, 0.0);
    vec3 vertexNormal = vec3(0.0, 0.0, 0.0);
    vec3 vertexTangent = vec3(0.0, 0.0, 0.0);

#if 1 == SKELETAL
    for(int i=0; i<MAX_BONES_PER_VERTEX; ++i)
    {
        prev_position += (prev_bone_matrices[int(vs_input.bone_indicies[i])] * vec4(vs_input.position, 1.0)) * vs_input.bone_weights[i];
        position += (bone_matrices[int(vs_input.bone_indicies[i])] * vec4(vs_input.position, 1.0)) * vs_input.bone_weights[i];
        vertexNormal += (bone_matrices[int(vs_input.bone_indicies[i])] * vec4(vs_input.normal, 0.0)).xyz * vs_input.bone_weights[i];
        vertexTangent += (bone_matrices[int(vs_input.bone_indicies[i])] * vec4(vs_input.tangent, 0.0)).xyz * vs_input.bone_weights[i];
    }
    position /= position.w;
    prev_position /= prev_position.w;
#else
    position = vec4(vs_input.position, 1.0);
    vertexNormal = vs_input.normal;
    vertexTangent = vs_input.tangent;
    prev_position = position;
#endif
    vertexNormal = normalize(vertexNormal);
    vertexTangent = normalize(vertexTangent);

    vs_output.vertexColor = vs_input.color;
    vs_output.worldPosition = (model * position).xyz;

    vs_output.normalVector = (model * vec4(vertexNormal, 0.0)).xyz;
    vec3 bitangent = cross(vertexTangent, vertexNormal);
    vs_output.tangentToWorld = model * mat4(vec4(vertexTangent, 0.0), vec4(vertexNormal, 0.0), vec4(bitangent, 0.0), vec4(0.0, 0.0, 0.0, 1.0));
    vs_output.texCoord = vs_input.texcoord;

    vs_output.cameraVector = camera_position.xyz - vs_output.worldPosition;
    vs_output.cameraDistance = length(vs_output.cameraVector);
    vs_output.cameraVector /= vs_output.cameraDistance;

    // point light dir
    vs_output.lightVector = lightPosition.xyz - vs_output.worldPosition;
    vs_output.lightDistance = length(vs_output.lightVector);
    vs_output.lightVector = lightDir.xyz;

    position = view_projection * model * position;
    prev_position = prev_view_projection * model * prev_position;
    vs_output.velocity = (position.xy / position.w) - (prev_position.xy / prev_position.w);
    vs_output.velocity *= 0.5;

    gl_Position = position;
}
#endif