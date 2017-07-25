#version 430 core

#define SKELETAL 0

#include "scene_constants.glsl"

//----------- UNIFORM_BLOCK ---------------//

#if 1 == SKELETAL
uniform mat4 bone_matrices[MAX_BONES];
#endif

uniform mat4 model;
uniform mat4 mvp;
uniform mat4 shadow_matrix;
uniform sampler2D shadow_texture;

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
    vec3 lightVector;
};

//----------- VERTEX_SHADER ---------------//

#ifdef VERTEX_SHADER
in VERTEX_INPUT vs_input;
out VERTEX_OUTPUT vs_output;

void main() {
    vec4 localPosition = vec4(0.0, 0.0, 0.0, 0.0);
    vec3 vertexNormal = vec3(0.0, 0.0, 0.0);
    vec3 vertexTangent = vec3(0.0, 0.0, 0.0);

#if 1 == SKELETAL
    for(int i=0; i<MAX_BONES_PER_VERTEX; ++i)
    {
        localPosition += (bone_matrices[int(vs_input.bone_indicies[i])] * vec4(vs_input.position, 1.0)) * vs_input.bone_weights[i];
        vertexNormal += (bone_matrices[int(vs_input.bone_indicies[i])] * vec4(vs_input.normal, 0.0)).xyz * vs_input.bone_weights[i];
        vertexTangent += (bone_matrices[int(vs_input.bone_indicies[i])] * vec4(vs_input.tangent, 0.0)).xyz * vs_input.bone_weights[i];
    }
    localPosition /= localPosition.w;
#else
    localPosition = vec4(vs_input.position, 1.0);
    vertexNormal = vs_input.normal;
    vertexTangent = vs_input.tangent;
#endif
    vertexNormal = normalize(vertexNormal);
    vertexTangent = normalize(vertexTangent);

    vs_output.vertexColor = vs_input.color;
    vs_output.worldPosition = (model * localPosition).xyz;

    vs_output.normalVector = (model * vec4(vertexNormal, 0.0)).xyz;
    vec3 bitangent = cross(vertexTangent, vertexNormal);
    vs_output.tangentToWorld = model * mat4(vec4(vertexTangent, 0.0), vec4(vertexNormal, 0.0), vec4(bitangent, 0.0), vec4(0.0, 0.0, 0.0, 1.0));
    vs_output.texCoord = vs_input.texcoord;

    vs_output.cameraVector = cameraPosition.xyz - vs_output.worldPosition;
    // point light dir
    // vs_output.lightVector = lightPosition.xyz - vs_output.worldPosition;
    vs_output.lightVector = lightDir.xyz;
    gl_Position = mvp * localPosition;
}
#endif

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    vec4 baseColor = get_base_color(vs_output.texCoord.xy);

    if(baseColor.a < 0.333f && enable_blend != 1)
    {
        discard;
    }

    vec3 normalVector = normalize(vs_output.normalVector);
    vec3 cameraVector = normalize(vs_output.cameraVector);
    vec3 lightVector = normalize(vs_output.lightVector);
    vec4 emissiveColor = get_emissive_color();
    vec3 normal = (vs_output.tangentToWorld * vec4(get_normal(vs_output.texCoord.xy), 0.0)).xyz;
    normalVector = normalize(normal);
    vec3 diffuseLighting = baseColor.xyz * clamp(dot(lightVector, normalVector), 0.0, 1.0);
    float specularLighting = clamp(dot(reflect(-lightVector, normalVector), cameraVector), 0.0, 1.0);
    specularLighting = pow(specularLighting, 60.0);
    fs_output = vec4(lightColor.xyz * (diffuseLighting + specularLighting) + emissiveColor.xyz * emissiveColor.w, 1.0);

    vec4 shadow_uv = shadow_matrix * vec4(vs_output.worldPosition, 1.0);
    shadow_uv.xyz /= shadow_uv.w;
    shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
    float shadow = texture(shadow_texture, shadow_uv.xy).x < shadow_uv.z - shadow_bias ? 0.5 : 1.0;
    fs_output.xyz *= shadow;
}
#endif