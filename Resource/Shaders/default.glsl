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
    vec4 baseColor = get_base_color(vs_output.texCoord.xy);

    if(baseColor.a < 0.333f && enable_blend != 1)
    {
        discard;
    }

    vec4 shadow_uv = shadow_matrix * vec4(vs_output.worldPosition, 1.0);
    shadow_uv.xyz /= shadow_uv.w;
    shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
    float shadow_depth = shadow_uv.z;

    float shadow_factor = 0.0;
    const float shadow_radius = 1.0;
    const vec2 sample_scale = shadow_radius / textureSize(shadow_texture, 0);
    for(int i=0; i<PoissonSampleCount; ++i)
    {
        vec2 uv = shadow_uv.xy + PoissonSamples[i] * sample_scale;
        shadow_factor += texture(shadow_texture, uv).x <= shadow_depth - shadow_bias ? 0.0 : 1.0;
    }
    shadow_factor /= (float(PoissonSampleCount));

    vec3 normalVector = vs_output.normalVector;
    vec3 cameraVector = normalize(vs_output.cameraRelativePosition);
    vec3 lightVector = normalize(lightDir.xyz);
    vec4 emissiveColor = get_emissive_color();

    vec3 normal = (vs_output.tangentToWorld * vec4(get_normal(vs_output.texCoord.xy), 0.0)).xyz;
    normalVector = normalize(normal);

    const float ambient_light = 0.05;
    const float light_intensity = 3.0;
    float diffuseLighting = clamp(shadow_factor * dot(lightVector, normalVector), ambient_light, 1.0) * light_intensity;
    vec3 diffuseColor = baseColor.xyz * diffuseLighting;

#if(USE_REFLECTION)
    vec3 reflectionColor = get_reflection_color(reflect(-cameraVector, normalVector)).xyz;
    diffuseColor *= reflectionColor;
#endif

    float specularLighting = clamp(shadow_factor * dot(reflect(-lightVector, normalVector), cameraVector), 0.0, 1.0);
    specularLighting = pow(specularLighting, 60.0) * light_intensity;
    fs_output = vec4(lightColor.xyz * (diffuseColor + specularLighting) + emissiveColor.xyz * emissiveColor.w, 1.0);

    fs_diffuse = baseColor;
    // because, rendertarget is UNSIGNED_BYTE
    fs_normal = vec4(normalVector, 1.0) * 0.5 + 0.5;
    fs_velocity = (vs_output.projectionPos.xy / vs_output.projectionPos.w) -
        (vs_output.prevProjectionPos.xy / vs_output.prevProjectionPos.w);
}
#endif