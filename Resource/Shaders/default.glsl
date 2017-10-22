#version 430 core

#define USE_REFLECTION 0

#include "PCFKernels.glsl"
#include "utility.glsl"
#include "scene_constants.glsl"
#include "default_material.glsl"
#include "default_vs.glsl"

uniform sampler2D shadow_texture;

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

    vec4 shadow_uv = SHADOW_MATRIX * vec4(vs_output.world_position, 1.0);
    shadow_uv.xyz /= shadow_uv.w;
    shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
    float shadow_depth = shadow_uv.z;

    float shadow_factor = 0.0;
    const float shadow_radius = 1.0;
    const vec2 sample_scale = shadow_radius / textureSize(shadow_texture, 0);
    for(int i=0; i<PoissonSampleCount; ++i)
    {
        vec2 uv = shadow_uv.xy + PoissonSamples[i] * sample_scale;
        shadow_factor += texture(shadow_texture, uv).x <= shadow_depth - SHADOW_BIAS ? 0.0 : 1.0;
    }
    shadow_factor /= (float(PoissonSampleCount));

    vec3 normal_vector = get_normal(vs_output.tex_coord.xy);
    // Note : Normalization is very important because tangent_to_world may have been scaled..
    normal_vector = normalize((vs_output.tangent_to_world * vec4(normal_vector, 0.0)).xyz);

    vec3 camera_vector = normalize(CAMERA_POSITION.xyz - vs_output.world_position);
    vec3 light_vector = normalize(LIGHT_DIRECTION.xyz);
    vec4 emissive_color = get_emissive_color();

    const float ambient_light = 0.05;
    const float light_intensity = 3.0;
    float diffuse_lighting = clamp(shadow_factor * dot(light_vector, normal_vector), ambient_light, 1.0) * light_intensity;
    vec3 diffuse_color = base_color.xyz * diffuse_lighting;

#if(USE_REFLECTION)
    vec3 reflection_color = get_reflection_color(reflect(-camera_vector, normal_vector)).xyz;
    diffuse_color *= reflection_color;
#endif

    float specularLighting = clamp(shadow_factor * dot(reflect(-light_vector, normal_vector), camera_vector), 0.0, 1.0);
    specularLighting = pow(specularLighting, 60.0) * light_intensity;
    fs_output = vec4(LIGHT_COLOR.xyz * (diffuse_color + specularLighting) + emissive_color.xyz * emissive_color.w, 1.0);

    fs_diffuse = base_color;
    // because, rendertarget is UNSIGNED_BYTE
    fs_normal = vec4(normal_vector, 1.0) * 0.5 + 0.5;
    fs_velocity = (vs_output.projection_pos.xy / vs_output.projection_pos.w) -
        (vs_output.prev_projection_pos.xy / vs_output.prev_projection_pos.w);
}
#endif