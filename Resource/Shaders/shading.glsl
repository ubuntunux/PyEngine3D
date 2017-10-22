#include "PCFKernels.glsl"
#include "utility.glsl"

const float PI = 3.141592;


float get_shadow_factor(vec3 world_position, sampler2D texture_shadow)
{
    float shadow_factor = 0.0;
    vec4 shadow_uv = SHADOW_MATRIX * vec4(world_position, 1.0);
    shadow_uv.xyz /= shadow_uv.w;
    shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
    float shadow_depth = shadow_uv.z;

    const float shadow_radius = 1.0;
    const vec2 sample_scale = shadow_radius / textureSize(texture_shadow, 0);
    for(int i=0; i<PoissonSampleCount; ++i)
    {
        vec2 uv = shadow_uv.xy + PoissonSamples[i] * sample_scale;
        shadow_factor += texture(texture_shadow, uv).x <= shadow_depth - SHADOW_BIAS ? 0.0 : 1.0;
    }
    shadow_factor /= (float(PoissonSampleCount));
    return shadow_factor;
}


// https://en.wikipedia.org/wiki/Oren%E2%80%93Nayar_reflectance_model
float oren_nayar(float roughness2, float NdotL, float NdotV, vec3 N, vec3 V, vec3 L)
{
    float incidentTheta = acos(NdotL);
    float outTheta = acos(NdotV);

    float A = 1.0 - 0.5 * (roughness2 / (roughness2 + 0.33));
    float B = (0.45 * roughness2) / (roughness2 + 0.09);
    float alpha = max(incidentTheta, outTheta);
    float beta  = min(incidentTheta, outTheta);

    vec3 u = normalize(V - N * NdotV);
    vec3 v = normalize(L - N * NdotL);
    float phiDiff = max(0.0, dot(u, v));

    // Exactly correct fomular.
    // return (A + (B * phiDiff * sin(alpha) * tan(beta))) * NdotL / PI;

    return (A + (B * phiDiff * sin(alpha) * tan(beta))) * NdotL;
}