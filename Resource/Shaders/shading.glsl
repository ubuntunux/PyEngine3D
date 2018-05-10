#include "PCFKernels.glsl"
#include "utility.glsl"
#include "precomputed_atmosphere/atmosphere_predefine.glsl"


float get_shadow_factor(vec2 screen_tex_coord, vec3 world_position, sampler2D texture_shadow)
{
    const float shadow_bias = 0.001;
    float shadow_factor = 0.0;
    vec4 shadow_uv = SHADOW_MATRIX * vec4(world_position, 1.0);
    shadow_uv.xyz /= shadow_uv.w;
    shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
    float shadow_depth = shadow_uv.z;

    //float slope = min(1.0, abs(depth + (dFdx(depth) + dFdy(depth)) / 3.0) * 0.01);
    //float slope_bias = mix(shadow_bias, -0.001, slope);

    vec2 uv = shadow_uv.xy;
    float depth = textureLod(texture_shadow, uv, 0.0).x;;

    if(0.0 <= uv.x && uv.x <= 1.0 && 0.0 <= uv.y && uv.y <= 1.0 && depth < 1.0)
    {
        shadow_factor = (shadow_depth + shadow_bias <= depth) ? 1.0 : 0.0;
    }
    else
    {
        shadow_factor = 1.0;
    }

    const int loop_count = 16;
    float texel_radius = 0.5 / length(textureSize(texture_shadow, 0));
    float rad_step = TWO_PI / float(loop_count);
    float rad = 0.0;

    for(int i=0; i<loop_count; ++i)
    {
        rad += rad_step;
        uv = shadow_uv.xy + vec2(sin(rad), cos(rad)) * texel_radius * 2.0 + vec2(texel_radius);

        if(0.0 <= uv.x && uv.x <= 1.0 && 0.0 <= uv.y && uv.y <= 1.0 && depth < 1.0)
        {
            depth = textureLod(texture_shadow, uv, 0.0).x;
            shadow_factor += (shadow_depth + shadow_bias <= depth) ? 1.0 : 0.0;
        }
        else
        {
            shadow_factor += 1.0;
        }
    }
    shadow_factor /= float(loop_count + 1);
    return shadow_factor;
}


// https://en.wikipedia.org/wiki/Oren%E2%80%93Nayar_reflectance_model
vec3 oren_nayar(float roughness2, float NdotL, float NdotV, vec3 N, vec3 V, vec3 L)
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

    return vec3((A + (B * phiDiff * sin(alpha) * tan(beta))) * NdotL);
}

vec3 fresnelSchlick(float cosTheta, vec3 F0)
{
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

vec3 fresnelSchlickRoughness(float cosTheta, vec3 F0, float roughness)
{
    return F0 + (max(vec3(1.0 - roughness), F0) - F0) * pow(1.0 - cosTheta, 5.0);
}

float D_blinn(float roughness, float NdH)
{
    float m = roughness * roughness;
    float m2 = m * m;
    float n = 2.0 / m2 - 2.0;
    return (n + 2.0) / (2.0 * PI) * pow(NdH, n);
}

float D_beckmann(float roughness, float NdH)
{
    float m = roughness * roughness;
    float m2 = m * m;
    float NdH2 = NdH * NdH;
    return exp((NdH2 - 1.0) / (m2 * NdH2)) / (PI * m2 * NdH2 * NdH2);
}

float DistributionGGX(float NdH, float roughness)
{
    float a      = roughness * roughness;
    float a2     = a * a;
    float NdH2 = NdH * NdH;

    float num   = a2;
    float denom = (NdH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;

    return num / denom;
}

float GeometrySchlickGGX(float NdV, float roughness)
{
    float r = (roughness + 1.0);
    float k = (r * r) / 8.0;
    float num   = NdV;
    float denom = NdV * (1.0 - k) + k;
    return num / denom;
}

float GeometrySmith(float NdV, float NdL, float roughness)
{
    float ggx2  = GeometrySchlickGGX(NdV, roughness);
    float ggx1  = GeometrySchlickGGX(NdL, roughness);
    return ggx1 * ggx2;
}

// simple phong specular calculation with normalization
vec3 phong_specular(in float LdR, in vec3 specular, in float roughness)
{
    float spec = max(0.0, LdR);
    float k = 1.999 / (roughness * roughness);
    return min(1.0, 3.0 * 0.0398 * k) * pow(spec, min(10000.0, k)) * specular;
}

// simple blinn specular calculation with normalization
vec3 blinn_specular(in float NdH, in vec3 specular, in float roughness)
{
    float k = 1.999 / (roughness * roughness);
    return min(1.0, 3.0 * 0.0398 * k) * pow(NdH, min(10000.0, k)) * specular;
}


// cook-torrance specular calculation
vec3 cooktorrance_specular(vec3 F, float NdL, float NdV, float NdH, float roughness)
{
    //float D = D_GGX(roughness, NdH);
    //float G = G_schlick(roughness, NdV, NdL);
    //float rim = mix(1.0 - roughness * 0.9, 1.0, NdV);
    //return (1.0 / rim) * F * G * D;

    // cook-torrance brdf
    float NDF = DistributionGGX(NdH, roughness);
    float G   = GeometrySmith(NdV, NdL, roughness);
    vec3 numerator    = NDF * G * F;
    float denominator = 4.0 * NdV * NdL;
    return numerator / max(denominator, 0.001);
}

vec2 env_BRDF_pproximate(float NdV, float roughness)
{
    // see https://www.unrealengine.com/blog/physically-based-shading-on-mobile
    const vec4 c0 = vec4(-1.0, -0.0275, -0.572,  0.022);
    const vec4 c1 = vec4( 1.0,  0.0425,  1.040, -0.040);
    vec4 r = roughness * c0 + c1;
    float a004 = min(r.x * r.x, exp2(-9.28 * NdV)) * r.x + r.y;
    return vec2(-1.04, 1.04) * a004 + r.zw;
}


/* PBR reference
    - http://www.curious-creature.com/pbr_sandbox/shaders/pbr.fs
    - https://gist.github.com/galek/53557375251e1a942dfa */
vec4 surface_shading(vec4 base_color,
                    vec3 emissive_color,
                    float metallic,
                    float roughness,
                    float reflectance,
                    float ssao_factor,
                    vec4 scene_reflect_color,
                    samplerCube texture_probe,
                    sampler2D texture_shadow,
                    vec2 screen_tex_coord,
                    vec3 world_position,
                    vec3 light_color,
                    vec3 N,
                    vec3 V,
                    vec3 L,
                    float depth)
{
    // Atmosphere
    vec3 scene_in_scatter;
    vec3 scene_sun_irradiance;
    vec3 scene_sky_irradiance;
    float scene_shadow_length;
    {
        float scene_linear_depth = depth_to_linear_depth(depth);

        GetSceneRadiance(
            ATMOSPHERE, scene_linear_depth, -V, N, texture_shadow,
            scene_sun_irradiance, scene_sky_irradiance, scene_in_scatter, scene_shadow_length);
    }

    vec3 shadow_factor = vec3( get_shadow_factor(screen_tex_coord, world_position, texture_shadow) );
    shadow_factor = max(shadow_factor, scene_sky_irradiance);

    light_color = light_color * scene_sun_irradiance;// * shadow_factor;

    // safe roughness
    roughness = clamp(roughness, 0.05, 1.0);

    // compute material reflectance
    vec3 R = reflect(-V, N);
    vec3 H = normalize(V + L);
    float NdL = max(0.0, dot(N, L));
    float NdV = max(0.001, dot(N, V));
    float NdH = max(0.001, dot(N, H));
    float HdV = max(0.001, dot(H, V));
    float LdV = max(0.001, dot(L, V));

    vec3 result = vec3(0.0, 0.0, 0.0);
    float opacity = base_color.w;

    vec3 F0 = vec3(0.04);
    F0 = mix(max(vec3(0.04), reflectance), base_color.xyz, metallic);

    vec3 fresnel = fresnelSchlick(HdV, F0);
    vec3 diffuse_light = vec3(0.0, 0.0, 0.0);
    vec3 specular_light = vec3(0.0, 0.0, 0.0);

#if TRANSPARENT_MATERIAL == 1
    float reflectivity = max(max(F0.r, F0.g), F0.b);
    opacity = clamp(base_color.w + base_color.w * reflectivity, 0.0, 1.0);
#endif

    // Directional lighting
    {
        diffuse_light += oren_nayar(roughness, NdL, NdV, N, V, L) / PI * NdL * light_color;
        specular_light += cooktorrance_specular(fresnel, NdL, NdV, NdH, roughness) * NdL * light_color;


        for(int i=0; i<MAX_POINT_LIGHTS; ++i)
        {
            if(1.0 != POINT_LIGHTS[i].render)
            {
                break;
            }

            float point_light_radius = POINT_LIGHTS[i].radius;
            vec3 point_light_dir = POINT_LIGHTS[i].pos.xyz - world_position;
            float point_light_dist = length(point_light_dir);

            if(point_light_radius < point_light_dist)
            {
                continue;
            }

            point_light_dir /= point_light_dist;

            vec3 point_light_half = normalize(V + point_light_dir);
            float point_light_attenuation = clamp(1.0 - point_light_dist / point_light_radius, 0.0, 1.0);
            point_light_attenuation *= point_light_attenuation;
            vec3 point_light_color = POINT_LIGHTS[i].color.xyz * point_light_attenuation;

            float point_light_NdL = max(0.01, dot(N, point_light_dir));
            float point_light_NdH = max(0.01, dot(N, point_light_half));

            diffuse_light += oren_nayar(roughness, point_light_NdL, NdV, N, V, point_light_dir) / PI * point_light_NdL * point_light_color;
            specular_light += cooktorrance_specular(fresnel, point_light_NdL, NdV, point_light_NdH, roughness) * point_light_NdL * point_light_color;
        }
    }

    // Image based lighting
    {
        const vec2 env_size = textureSize(texture_probe, 0);
        const float max_env_mipmap = 5.0; // log2(max(env_size.x, env_size.y));

        vec3 ibl_diffuse_light = textureLod(texture_probe, invert_y(N), max_env_mipmap).xyz;
        vec3 ibl_specular_light = textureLod(texture_probe, invert_y(R), max_env_mipmap * roughness).xyz;

        // Note : because texture_probe is HDR and not sRGB.
        //ibl_diffuse_light = pow(ibl_diffuse_light, vec3(2.2));
        //ibl_specular_light = pow(ibl_specular_light, vec3(2.2));

        // mix scene reflection
        if(RENDER_SSR == 1.0f)
        {
            ibl_specular_light.xyz = mix(ibl_specular_light.xyz, scene_reflect_color.xyz, scene_reflect_color.w);
        }

        vec2 envBRDF = clamp(env_BRDF_pproximate(NdV, roughness), 0.0, 1.0);
        vec3 shValue = fresnelSchlick(NdV, F0) * envBRDF.x + envBRDF.y;

        diffuse_light += ibl_diffuse_light * shValue;
        specular_light += ibl_specular_light * shValue;
    }

    // final result
    diffuse_light *= base_color.xyz * clamp((vec3(1.0) - fresnel) * (1.0 - metallic), 0.0, 1.0);
    specular_light = mix(specular_light, specular_light * base_color.xyz, vec3(metallic));

    result = (diffuse_light + specular_light) * shadow_factor;
    // result += scene_in_scatter;

    // SSAO
    if(RENDER_SSAO == 1.0f)
    {
        result *= ssao_factor;
    }

    // Emissive
    result += emissive_color;

    return vec4(max(vec3(0.0), result), opacity);
}