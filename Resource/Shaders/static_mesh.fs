#version 430 core

layout(std140) uniform sceneConstants
{
    mat4 view;
    mat4 perspective;
    vec4 cameraPosition;
    vec4 lightPosition;
    vec4 lightColor;
};

in struct DATA
{
    vec3 worldPosition;
    vec4 vertexColor;
    vec3 normalVector;
    mat4 tangentToWorld;
    vec2 textureCoordinate;
    vec3 cameraVector;
    vec3 lightVector;
} data;

out vec4 result;

void main() {
    result = vec4(1.0, 1.0, 1.0, 1.0);
    vec3 normalVector = normalize(data.normalVector);
    vec3 cameraVector = normalize(data.cameraVector);
    vec3 lightVector = normalize(data.lightVector);
    vec3 diffuseTex = texture(textureDiffuse, data.textureCoordinate.xy).xyz;
    vec3 normalTex = texture(textureNormal, data.textureCoordinate.xy).xyz;
    normalTex = normalize((data.tangentToWorld * vec4(normalTex * 2.0 - 1.0, 0.0)).xyz);

    vec3 diffuseLighting = diffuseTex * diffuseColor.xyz * clamp(dot(lightVector, normalTex), 0.0, 1.0);
    float specularLighting = clamp(dot(reflect(-lightVector, normalTex), cameraVector), 0.0, 1.0);
    specularLighting = pow(specularLighting, 60.0);
    result = vec4(lightColor.xyz * (diffuseLighting + specularLighting), 1.0);
}