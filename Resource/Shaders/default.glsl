#version 430 core

#include "utility.glsl"
#include "scene_constants.glsl"
#include "default_vs.glsl"

uniform mat4 shadow_matrix;
uniform sampler2D shadow_texture;
uniform samplerCube texture_cube;

//-------------- MATERIAL_COMPONENTS ---------------//

#include "default_material.glsl"

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;

layout (location = 0) out vec4 fs_output;
layout (location = 1) out vec4 fs_diffuse;
layout (location = 2) out vec4 fs_normal;
layout (location = 3) out vec2 fs_velocity;

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
    float diffuseLighting = clamp(dot(lightVector, normalVector), 0.0, 1.0);
    vec3 diffuseColor = baseColor.xyz * diffuseLighting;
    float specularLighting = clamp(dot(reflect(-lightVector, normalVector), cameraVector), 0.0, 1.0);
    specularLighting = pow(specularLighting, 60.0);
    fs_output = vec4(lightColor.xyz * (diffuseColor + specularLighting) + emissiveColor.xyz * emissiveColor.w, 1.0);

    vec4 shadow_uv = shadow_matrix * vec4(vs_output.worldPosition, 1.0);
    shadow_uv.xyz /= shadow_uv.w;
    shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
    float shadow_d = shadow_uv.z;

    float shadow_factor = texture(shadow_texture, shadow_uv.xy).x <= shadow_d - shadow_bias ? 0.0 : 1.0;
    float weight = 1.0;
    const int kernel = 2;
    const vec2 inv_shadow_map_size = 1.0 / textureSize(shadow_texture, 0);
    for(int y=-kernel;y<=kernel;++y)
    {
        for(int x=-kernel;x<=kernel;++x)
        {
            vec2 uv = shadow_uv.xy + vec2(x, y) * inv_shadow_map_size;
            uv += vec2(rand(uv)) * inv_shadow_map_size;

            shadow_factor += texture(shadow_texture, uv).x <= shadow_d - shadow_bias ? 0.2 : 1.0;
            weight += 1.0;
        }
    }
    shadow_factor /= weight;
    shadow_factor = max(0.2, shadow_factor);

    fs_diffuse = vec4(texture(texture_cube, reflect(-cameraVector, normalVector)).xyz, 1.0);
    fs_normal = vec4(normalVector, 1.0);
    fs_velocity = vs_output.velocity;

    fs_output.xyz *= shadow_factor;
}
#endif