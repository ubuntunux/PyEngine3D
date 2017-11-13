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
    const int sample_count = PoissonSampleCount / 4;
    float weights = 0.0;
    for(int i=0; i<sample_count; ++i)
    {
        float weight = length(PoissonSamples[i]);
        weights += weight;
        vec2 uv = shadow_uv.xy + PoissonSamples[i] * sample_scale * 3.0;
        shadow_factor += texture(texture_shadow, uv).x <= shadow_depth ? 0.0 : weight;
    }
    shadow_factor /= weights;
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

// compute fresnel specular factor for given base specular and product
// product could be NdV or VdH depending on used technique
vec3 fresnel_factor(in vec3 f0, in float product)
{
    return mix(f0, vec3(1.0), pow(max(0.0, 1.01 - product), 5.0));
}

float D_blinn(in float roughness, in float NdH)
{
    float m = roughness * roughness;
    float m2 = m * m;
    float n = 2.0 / m2 - 2.0;
    return (n + 2.0) / (2.0 * PI) * pow(NdH, n);
}

float D_beckmann(in float roughness, in float NdH)
{
    float m = roughness * roughness;
    float m2 = m * m;
    float NdH2 = NdH * NdH;
    return exp((NdH2 - 1.0) / (m2 * NdH2)) / (PI * m2 * NdH2 * NdH2);
}

float D_GGX(in float roughness, in float NdH)
{
    float m = roughness * roughness;
    float m2 = m * m;
    float d = (NdH * m2 - NdH) * NdH + 1.0;
    return m2 / (PI * d * d);
}

float G_schlick(in float roughness, in float NdV, in float NdL)
{
    float k = roughness * roughness * 0.5;
    float V = NdV * (1.0 - k) + k;
    float L = NdL * (1.0 - k) + k;
    return 0.25 / (V * L);
}

// simple phong specular calculation with normalization
vec3 phong_specular(in vec3 V, in vec3 L, in vec3 N, in vec3 specular, in float roughness)
{
    vec3 R = reflect(-L, N);
    float spec = max(0.0, dot(V, R));
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
vec3 cooktorrance_specular(in float NdL, in float NdV, in float NdH, in vec3 specular, in float roughness)
{
    float D = D_GGX(roughness, NdH);
    float G = G_schlick(roughness, NdV, NdL);
    float rim = mix(1.0 - roughness * 0.9, 1.0, NdV);
    return (1.0 / rim) * specular * G * D;
}

vec2 env_BRDF_pproximate(float NoV, float roughness) {
    // see https://www.unrealengine.com/blog/physically-based-shading-on-mobile
    const vec4 c0 = vec4(-1.0, -0.0275, -0.572,  0.022);
    const vec4 c1 = vec4( 1.0,  0.0425,  1.040, -0.040);
    vec4 r = roughness * c0 + c1;
    float a004 = min(r.x * r.x, exp2(-9.28 * NoV)) * r.x + r.y;
    return vec2(-1.04, 1.04) * a004 + r.zw;
}


/* PBR reference
    - http://www.curious-creature.com/pbr_sandbox/shaders/pbr.fs
    - https://gist.github.com/galek/53557375251e1a942dfa */
vec4 surface_shading(vec4 base_color,
                    float metallic,
                    float roughness,
                    float clear_coat_roughness,
                    float reflectance,
                    samplerCube texture_cube,
                    vec3 light_color,
                    vec3 N,
                    vec3 V,
                    vec3 L,
                    float shadow_factor) {

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

    // Fresnel specular reflectance at normal incidence
    const float ior = 1.38;
    vec3 f0 = vec3(abs ((1.0 - ior) / (1.0 + ior)));
    f0 = mix(max(vec3(0.04), f0 * reflectance * reflectance), base_color.xyz, metallic);

    float opacity = 1.0;
#if TRANSPARENT_MATERIAL == 1
    float reflectivity = max(max(f0.r, f0.g), f0.b);
    opacity = reflectivity + base_color.w * (1.0 - reflectivity);
    base_color.xyz *= base_color.w;
#endif

    // specular : mix between metal and non-metal material, for non-metal constant base specular factor of 0.04 grey is used
    vec3 specfresnel = fresnel_factor(f0, HdV);
    vec3 specular_lighting = cooktorrance_specular(NdL, NdV, NdH, specfresnel, roughness);
    specular_lighting = specular_lighting * light_color * NdL * shadow_factor;

    // diffuse
    vec3 diffuse_light = vec3(oren_nayar(roughness, NdL, NdV, N, V, L));
    diffuse_light = diffuse_light * base_color.xyz * (vec3(1.0) - specfresnel) * light_color * shadow_factor;

    // Image based lighting
    const vec2 env_size = textureSize(texture_cube, 0);
    const float env_mipmap_count = log2(min(env_size.x, env_size.y));
    vec3 ibl_diffuse_color = textureLod(texture_cube, invert_y(N), env_mipmap_count - 1.0).xyz;
    vec3 ibl_specular_color = textureLod(texture_cube, invert_y(R), env_mipmap_count * roughness).xyz;
    ibl_diffuse_color = pow(ibl_diffuse_color, vec3(2.2));
    ibl_specular_color = pow(ibl_specular_color, vec3(2.2));

    diffuse_light += base_color.xyz * ibl_diffuse_color;
    vec2 envBRDF = clamp(env_BRDF_pproximate(NdV, roughness), 0.0, 1.0);
    specular_lighting += (fresnel_factor(f0, NdV) * envBRDF.x + envBRDF.y) * ibl_specular_color;

    // final result
    vec3 result = diffuse_light * (1.0 - metallic) + specular_lighting;
    return vec4(max(vec3(0.0), result), opacity);
}


float F_Schlick_Scalar(float fresnel_factor, float f0, float f90)
{
    return f0 + (f90 - f0) * pow(1.0 - fresnel_factor, 5.0);
}

vec3 F_Schlick(float VoH, vec3 f0, float f90) {
    return f0 + (vec3(f90) - f0) * pow(1.0 - VoH, 5.0);
}

vec3 beerLambert(float NoV, float NoL, vec3 alpha, float d)
{
    return exp(alpha * -(d * ((NoL + NoV) / max(NoL * NoV, 1e-3))));
}

float D_GGX_Anisotropy(float NoH, vec3 h, vec3 x, vec3 y, float ax, float ay) {
    float XoH = dot(x, h);
    float YoH = dot(y, h);
    float d = XoH * XoH * (ax * ax) + YoH * YoH * (ay * ay) + NoH * NoH;
    return (ax * ay) / (PI * d * d);
}

// Smith-GGX correlated for microfacets height
float V_SmithGGXCorrelated(float NoV, float NoL, float a) {
    float a2 = a * a;
    float GGXL = NoV * sqrt((-NoL * a2 + NoL) * NoL + a2);
    float GGXV = NoL * sqrt((-NoV * a2 + NoV) * NoV + a2);
    // approximation
    // float GGXL = NoV * (NoL * (1.0 - a) + a);
    // float GGXV = NoL * (NoV * (1.0 - a) + a);
    return 0.5 / (GGXV + GGXL);
}

float Fd_Lambert() {
    return 1.0 / PI;
}

/*vec3 irradianceSH(vec3 n) {
    return
        sphericalHarmonics[0]
        + sphericalHarmonics[1] * (n.y)
        + sphericalHarmonics[2] * (n.z)
        + sphericalHarmonics[3] * (n.x)
        + sphericalHarmonics[4] * (n.y * n.x)
        + sphericalHarmonics[5] * (n.y * n.z)
        + sphericalHarmonics[6] * (3.0 * n.z * n.z - 1.0)
        + sphericalHarmonics[7] * (n.z * n.x)
        + sphericalHarmonics[8] * (n.x * n.x - n.y * n.y);
}*/

vec4 surface_shading2(vec4 base_color,
                    float metallic,
                    float roughness,
                    float clear_coat,
                    float clear_coat_roughness,
                    vec3 clear_coat_color,
                    float clear_coat_thickness,
                    float clear_coat_IOR,
                    float reflectance,
                    samplerCube texture_cube,
                    vec3 light_color,
                    vec3 N,
                    vec3 V,
                    vec3 L,
                    float shadow_factor) {

    base_color.xyz = (1.0 - metallic) * base_color.xyz;

    roughness = clamp(roughness, 0.05, 1.0);
    float roughness2 = roughness * roughness;
    float smoothness2 = 1.0 - roughness2;
    float clear_coat_roughness2 = clear_coat_roughness * clear_coat_roughness;
    const float ao = 1.0;

    float energy = 1.0;
    float attenuation = 1.0;
    // Disc area light
    float e = sin(radians(0.53));
    float d = cos(radians(0.53));
    vec3 R = reflect(-V, N);
    float LdR = dot(L, R);
    vec3 S = R - LdR * L;
    L = LdR < d ? normalize(d * L + normalize(S) * e) : R;
    /*if (lightType == LIGHT_TYPE_POINT) {
        vec3 posToLight = lightPosition - outWorldPosition;
        float distanceSquare = dot(posToLight, posToLight);
        l = normalize(posToLight);
        NoL = dot(n, l);
        energy = 1.0;
        attenuation  = getSquareFalloffAttenuation(distanceSquare);
        attenuation *= 1.0 / max(distanceSquare, 1e-4);
        attenuation *= getPhotometricAttenuation(-l, lightDir);
        if (lightGeometry.w >= 1.0) {
            attenuation *= getAngleAttenuation(l, -lightDir);
        }
    }*/

    // compute material reflectance
    vec3 H = normalize(V + L);
    float NdL = max(0.0, dot(N, L));
    float NdV = max(0.001, dot(N, V));
    float NdH = max(0.001, dot(N, H));
    float HdV = max(0.001, dot(H, V));
    float LdH = max(0.0, dot(L, H));
    float LdV = max(0.001, dot(L, V));

    // Fresnel specular reflectance at normal incidence
    const float ior = 1.38;
    vec3 f0 = vec3(abs ((1.0 - ior) / (1.0 + ior)));
    f0 = mix(max(vec3(0.04), f0 * reflectance * reflectance), base_color.xyz, metallic);

    float opacity = 1.0;
#if TRANSPARENT_MATERIAL == 1
    float reflectivity = max(max(f0.r, f0.g), f0.b);
    opacity = reflectivity + base_color.w * (1.0 - reflectivity);
    base_color.xyz *= base_color.w;
#endif

    vec3  F_term = F_Schlick(LdH, f0, clamp(dot(f0, vec3(50.0 * 0.33)), 0.0, 1.0));
    float V_term = V_SmithGGXCorrelated(NdV, NdL, roughness2);
    float D_term = D_GGX(roughness2, NdH);
    vec3 Fr = (D_term * V_term) * F_term;

    // diffuse BRDF
    vec3 Fd = base_color.xyz * Fd_Lambert();

    // clear coat
    float Dcc  = D_GGX(clear_coat_roughness2, NdH);
    float Fcc  = F_Schlick_Scalar(LdH, 0.04, 1.0) * clear_coat;
    float Vcc  = V_SmithGGXCorrelated(NdV, NdL, clear_coat_roughness2);
    float FrCC = Dcc * Vcc * Fcc;

    float eta = 1.0 / max(0.001, clear_coat_IOR);
    vec3 refracted_v = -refract(V, N, eta);
    float refracted_NdV = clamp(dot(N, refracted_v), 0.0, 1.0);

    vec3 refracted_l = -refract(L, N, eta);
    float refracted_NdL = clamp(dot(N, refracted_l), 0.0, 1.0);
    vec3 clearCoatAbsorption =
        mix(vec3(1.0), beerLambert(refracted_NdV, refracted_NdL, clear_coat_color, clear_coat_thickness), clear_coat);

    // direct contribution
    vec3 result = (attenuation * NdL) * light_color * energy * ((Fd + Fr) * (1.0 - Fcc) * clearCoatAbsorption + FrCC);

    // micro-shadowing
    float aperture = 2.0 * ao * ao;
    float microShadow = clamp(abs(NdL) + aperture - 1.0, 0.0, 1.0);
    result *= microShadow * shadow_factor;


    // Image based lighting
    vec3 IBL_R = mix(N, R, smoothness2 * (sqrt(smoothness2) + roughness2));  // caculate specular dominant direction
    const vec2 env_size = textureSize(texture_cube, 0);
    const float env_mipmap_count = log2(min(env_size.x, env_size.y));

    vec3 ibl_diffuse_color = textureLod(texture_cube, invert_y(N), env_mipmap_count - 1.0).xyz;
    vec3 ibl_specular_color = textureLod(texture_cube, invert_y(IBL_R), env_mipmap_count * roughness).xyz;
    vec3 ibl_clear_coat_specular_color = textureLod(texture_cube, invert_y(IBL_R), env_mipmap_count * clear_coat_roughness).xyz;
    ibl_diffuse_color = pow(ibl_diffuse_color, vec3(2.2));
    ibl_specular_color = pow(ibl_specular_color, vec3(2.2));
    ibl_clear_coat_specular_color = pow(ibl_clear_coat_specular_color, vec3(2.2));

    vec2 envBRDF = clamp(env_BRDF_pproximate(NdV, roughness), 0.0, 1.0);
    vec3 ibl_specular_lighting = f0 * envBRDF.x + envBRDF.y * (1.0 - clear_coat) * clamp(dot(f0, vec3(50.0 * 0.33)), 0.0, 1.0);

    // diffuse indirect
    vec3 indirectDiffuse = base_color.xyz * ibl_diffuse_color * Fd_Lambert();

    // computeSpecularAO
    ibl_specular_color *= clamp(pow(NdV + ao, exp2(-16.0 * roughness - 1.0)) - 1.0 + ao, 0.0, 1.0);

    // clear coat
    float IBL_Fcc = F_Schlick_Scalar(NdV, 0.04, 1.0) * clear_coat;
    vec3 IBL_clearCoatAbsorption = mix(vec3(1.0), beerLambert(NdV, NdV, clear_coat_color, clear_coat_thickness), clear_coat);

    // indirect contribution
    result += (indirectDiffuse + ibl_specular_color * ibl_specular_lighting) *
                    (1.0 - IBL_Fcc) * IBL_clearCoatAbsorption + ibl_clear_coat_specular_color * IBL_Fcc;

    // final result
    return vec4(max(vec3(0.0), result), opacity);
}