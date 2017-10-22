#version 430 core

#define USE_REFLECTION 0

#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "default_material.glsl"
#include "default_vs.glsl"

uniform sampler2D texture_shadow;

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;

layout (location = 0) out vec4 fs_output;
layout (location = 1) out vec4 fs_diffuse;
layout (location = 2) out vec4 fs_normal;
layout (location = 3) out vec2 fs_velocity;

void main() {
    vec4 base_color = get_base_color(vs_output.tex_coord.xy);

    if(base_color.a < 0.333f && enable_blend != 1)
    {
        discard;
    }

    const float ambient_light = 0.05;
    const float light_intensity = 3.0;
    float roughness = get_roughness();
    float roughness2 = roughness * roughness;
    vec4 emissive_color = get_emissive_color();

    float shadow_factor = get_shadow_factor(vs_output.world_position, texture_shadow);

    vec3 N = get_normal(vs_output.tex_coord.xy);
    // Note : Normalization is very important because tangent_to_world may have been scaled..
    N = normalize((vs_output.tangent_to_world * vec4(N, 0.0)).xyz);

    vec3 V = normalize(CAMERA_POSITION.xyz - vs_output.world_position);
    vec3 L = normalize(LIGHT_DIRECTION.xyz);
    vec3 H = normalize(L + V);
    vec3 R = reflect(-V, N);
    float NdotL = clamp(dot(N, L), 0.0, 1.0);
    float NdotV = clamp(dot(N, V), 0.0, 1.0);
    float LdotV = clamp(dot(L, V), 0.0, 1.0);

    float diffuse_lighting = oren_nayar(roughness2, NdotL, NdotV, N, V, L);
    diffuse_lighting = clamp(shadow_factor * diffuse_lighting, ambient_light, 1.0) * light_intensity;
    vec3 diffuse_color = base_color.xyz * diffuse_lighting;

#if(USE_REFLECTION)
    vec3 reflection_color = get_reflection_color(R).xyz;
    diffuse_color *= reflection_color;
#endif

    float specular_lighting = clamp(shadow_factor * dot(R, L), 0.0, 1.0);
    specular_lighting = pow(specular_lighting, 60.0) * light_intensity;
    fs_output = vec4(LIGHT_COLOR.xyz * (diffuse_color + specular_lighting) + emissive_color.xyz * emissive_color.w, 1.0);

    fs_diffuse = base_color;

    // because, rendertarget is UNSIGNED_BYTE
    fs_normal = vec4(N, 1.0) * 0.5 + 0.5;
    fs_velocity = (vs_output.projection_pos.xy / vs_output.projection_pos.w) -
        (vs_output.prev_projection_pos.xy / vs_output.prev_projection_pos.w);
}
#endif