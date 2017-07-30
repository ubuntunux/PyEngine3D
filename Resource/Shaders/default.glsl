#version 430 core

#include "utility.glsl"
#include "scene_constants.glsl"
#include "default_vs.glsl"

uniform mat4 shadow_matrix;
uniform sampler2D shadow_texture;


//-------------- MATERIAL_COMPONENTS ---------------//

#include "default_material.glsl"

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
    shadow_uv.xy = shadow_uv.xy * 0.5 + 0.5;
    float shadow_d = depth_to_distance(near_far.x, near_far.y, shadow_uv.z);

    float shadow_distance = texture(shadow_texture, shadow_uv.xy).x;
    float shadow = shadow_distance <= shadow_d - shadow_bias ? 0.2 : 1.0;
    fs_output.xyz *= shadow;
}
#endif