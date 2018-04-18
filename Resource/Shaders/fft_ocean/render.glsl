#extension GL_EXT_texture_array : enable

#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"

uniform float height;
uniform float simulation_amplitude;
uniform vec4 simulation_size;
uniform vec2 cell_size;

uniform sampler2DArray fftWavesSampler;
uniform sampler3D slopeVarianceSampler;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_shadow;
uniform samplerCube texture_probe;

#ifdef MATERIAL_COMPONENTS
    uniform vec2 uv_tiling;
    uniform sampler2D texture_foam;
#endif


struct VERTEX_OUTPUT
{
    vec2 uv;
    vec3 wave_offset;
    vec3 world_pos;
    vec4 proj_pos;
};

#ifdef GL_VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
layout (location = 5) in vec2 offset;   // instance buffer

layout (location = 0) out VERTEX_OUTPUT vs_output;

vec2 oceanPos(vec4 vertex, out float dist)
{
    float h = height - CAMERA_POSITION.y;
    vec3 cameraDir = normalize((INV_PROJECTION * (vertex + vec4(JITTER_OFFSET, 0.0, 0.0))).xyz);
    vec3 worldDir = (INV_VIEW_ORIGIN * vec4(cameraDir, 0.0)).xyz;

    if(0.0 < h)
    {
        dist = (0.0 < worldDir.y) ? (h / worldDir.y) : NEAR_FAR.y;
    }
    else
    {
        dist = (worldDir.y < 0.0) ? (h / worldDir.y) : NEAR_FAR.y;
    }

    return CAMERA_POSITION.xz + dist * worldDir.xz;
}

void main()
{
    float dist, dist_x, dist_y;
    vec3 vertex_scale = vec3(1.5, 1.5, 1.0);
    vec4 vertex_pos = vec4(vs_in_position * vertex_scale, 1.0);
    vec2 u = oceanPos(vertex_pos, dist);
    vec2 ux = oceanPos(vertex_pos + vec4(cell_size.x, 0.0, 0.0, 0.0), dist_x);
    vec2 uy = oceanPos(vertex_pos + vec4(0.0, cell_size.y, 0.0, 0.0), dist_y);
    vec2 dux = abs(ux - u) * 2.0;
    vec2 duy = abs(uy - u) * 2.0;

    vec3 dP = vec3(0.0);
    dP.y += textureGrad(fftWavesSampler, vec3(u / simulation_size.x, 0.0), dux / simulation_size.x, duy / simulation_size.x).x;
    dP.y += textureGrad(fftWavesSampler, vec3(u / simulation_size.y, 0.0), dux / simulation_size.y, duy / simulation_size.y).y;
    dP.y += textureGrad(fftWavesSampler, vec3(u / simulation_size.z, 0.0), dux / simulation_size.z, duy / simulation_size.z).z;
    dP.y += textureGrad(fftWavesSampler, vec3(u / simulation_size.w, 0.0), dux / simulation_size.w, duy / simulation_size.w).w;

    dP.xz += textureGrad(fftWavesSampler, vec3(u / simulation_size.x, 3.0), dux / simulation_size.x, duy / simulation_size.x).xy;
    dP.xz += textureGrad(fftWavesSampler, vec3(u / simulation_size.y, 3.0), dux / simulation_size.y, duy / simulation_size.y).zw;
    dP.xz += textureGrad(fftWavesSampler, vec3(u / simulation_size.z, 4.0), dux / simulation_size.z, duy / simulation_size.z).xy;
    dP.xz += textureGrad(fftWavesSampler, vec3(u / simulation_size.w, 4.0), dux / simulation_size.w, duy / simulation_size.w).zw;

    vec3 world_pos = vec3(u.x, height, u.y) + dP * simulation_amplitude;

    vec4 proj_pos = VIEW_PROJECTION * vec4(world_pos.xyz, 1.0);

    float fade = 1.0f;
    if(dist < NEAR_FAR.y)
    {
        fade = 1.0 - pow(clamp(length(vertex_pos.xy / vertex_scale.xy), 0.0, 1.0), 4.0);
        proj_pos.xy = mix(vertex_pos.xy * proj_pos.w, proj_pos.xy, fade);
    }

    vs_output.uv = u;
    vs_output.wave_offset = dP;
    vs_output.world_pos = world_pos;
    vs_output.proj_pos = proj_pos;
    gl_Position = proj_pos;
}
#endif


#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

float erfc(float x)
{
	return 2.0 * exp(-x * x) / (2.319 * x + sqrt(4.0 + 1.52 * x * x));
}

float Lambda(float cosTheta, float sigmaSq)
{
	float v = cosTheta / sqrt((1.0 - cosTheta * cosTheta) * (2.0 * sigmaSq));
    return max(0.0, (exp(-v * v) - v * sqrt(PI) * erfc(v)) / (2.0 * v * sqrt(PI)));
}

float reflectedSunRadiance(vec3 L, vec3 V, vec3 N, vec3 Tx, vec3 Tz, vec2 sigmaSq)
{
    vec3 H = normalize(L + V);
    float zetax = dot(H, Tx) / dot(H, N);
    float zetay = dot(H, Tz) / dot(H, N);

    float zL = dot(L, N); // cos of source zenith angle
    float zV = dot(V, N); // cos of receiver zenith angle
    float zH = dot(H, N); // cos of facet normal zenith angle
    float zH2 = zH * zH;

    float p = exp(-0.5 * (zetax * zetax / sigmaSq.x + zetay * zetay / sigmaSq.y)) / (2.0 * PI * sqrt(sigmaSq.x * sigmaSq.y));

    float tanV = atan(dot(V, Tz), dot(V, Tx));
    float cosV2 = 1.0 / (1.0 + tanV * tanV);
    float sigmaV2 = sigmaSq.x * cosV2 + sigmaSq.y * (1.0 - cosV2);

    float tanL = atan(dot(L, Tz), dot(L, Tx));
    float cosL2 = 1.0 / (1.0 + tanL * tanL);
    float sigmaL2 = sigmaSq.x * cosL2 + sigmaSq.y * (1.0 - cosL2);

    float fresnel = 0.02 + 0.98 * pow(1.0 - dot(V, H), 5.0);

    zL = max(zL, 0.01);
    zV = max(zV, 0.01);

    return fresnel * p / ((1.0 + Lambda(zL, sigmaL2) + Lambda(zV, sigmaV2)) * zV * zH2 * zH2 * 4.0);
}

float meanFresnel(float cosThetaV, float sigmaV)
{
	return pow(1.0 - cosThetaV, 5.0 * exp(-2.69 * sigmaV)) / (1.0 + 22.7 * pow(sigmaV, 1.5));
}

float meanFresnel(vec3 V, vec3 N, vec2 sigmaSq)
{
    vec2 v = V.xy;
    vec2 t = v * v / (1.0 - V.z * V.z);
    float sigmaV2 = dot(t, sigmaSq);
    return meanFresnel(dot(V, N), sqrt(sigmaV2));
}

float erf(float x)
{
	float a  = 0.140012;
	float x2 = x * x;
	float ax2 = a * x2;
	return sign(x) * sqrt(1.0 - exp(-x2 * (4.0 / PI + ax2) / (1.0 + ax2)));
}

float whitecapCoverage(float epsilon, float mu, float sigma2)
{
	return 0.5 * erf((0.5 * sqrt(2.0) * (epsilon - mu) * inversesqrt(sigma2))) + 0.5;
}


void main()
{
    vec2 uv = vs_output.uv;
    vec2 screen_tex_coord = (vs_output.proj_pos.xy / vs_output.proj_pos.w) * 0.5 + 0.5;
    vec3 relative_pos = CAMERA_POSITION.xyz - vs_output.world_pos.xyz;
    float scene_linear_depth = dot(relative_pos.xyz, vec3(VIEW_ORIGIN[0].z, VIEW_ORIGIN[1].z, VIEW_ORIGIN[2].z));
    float bg_linear_depth = texture(texture_linear_depth, screen_tex_coord).x;
    float roughness = 0.1;

    vec2 slopes = textureLod(fftWavesSampler, vec3(uv / simulation_size.x, 1.0), 0.0).xy;
    slopes += textureLod(fftWavesSampler, vec3(uv / simulation_size.y, 1.0), 0.0).zw;
    slopes += textureLod(fftWavesSampler, vec3(uv / simulation_size.z, 2.0), 0.0).xy;
    slopes += textureLod(fftWavesSampler, vec3(uv / simulation_size.w, 2.0), 0.0).zw;

    float dist = length(relative_pos);
    float distance_fade = clamp(1.0 - dist * 0.005, 0.0, 1.0);
    vec3 V = relative_pos / dist;

    vec3 vertex_normal = normalize(vec3(-vs_output.wave_offset.x, vs_output.wave_offset.y, -vs_output.wave_offset.z));
    vertex_normal.y = 0.5 - vertex_normal.y * 0.5;
    vertex_normal = normalize(vertex_normal);

    vec3 N = normalize(vec3(-slopes.x, 1.0, -slopes.y) + vertex_normal * 0.2);
    if (dot(V, N) < 0.0)
    {
        N = reflect(N, V); // reflects backfacing normals
    }

    vec3 L = LIGHT_DIRECTION.xyz;
    vec3 H = normalize(V + L);
    vec3 R = reflect(-V, N);
    R.y = abs(R.y);

    float NdL = max(0.0, dot(N, L));
    float NdV = max(0.0, dot(N, V));
    float NdH = max(0.0, dot(N, H));
    float HdV = max(0.0, dot(H, V));
    float LdV = max(0.0, dot(L, V));

    float Jxx = dFdx(uv.x);
    float Jxy = dFdy(uv.x);
    float Jyx = dFdx(uv.y);
    float Jyy = dFdy(uv.y);
    float A = Jxx * Jxx + Jyx * Jyx;
    float B = Jxx * Jxy + Jyx * Jyy;
    float C = Jxy * Jxy + Jyy * Jyy;
    const float SCALE = 10.0;
    float ua = pow(A / SCALE, 0.25);
    float ub = 0.5 + 0.5 * B / sqrt(A * C);
    float uc = pow(C / SCALE, 0.25);
    vec2 sigmaSq = texture(slopeVarianceSampler, vec3(ua, ub, uc)).xw;

    sigmaSq = max(sigmaSq, 2e-5);

    vec3 Tz = normalize(vec3(0.0, N.z, -N.y));
    vec3 Tx = cross(Tz, N);

    // float specular_intensity = reflectedSunRadiance(L, V, N, Tx, Tz, sigmaSq);

    // Atmosphere
    vec3 scene_radiance = vec3(0.0);
    vec3 scene_in_scatter = vec3(0.0);
    vec3 scene_sun_irradiance;
    vec3 scene_sky_irradiance;
    float scene_shadow_length;

    {
        GetSceneRadiance(
            ATMOSPHERE, scene_linear_depth, -V, N, texture_shadow,
            scene_sun_irradiance, scene_sky_irradiance, scene_in_scatter, scene_shadow_length);
        scene_radiance = (scene_sun_irradiance + scene_sky_irradiance + scene_in_scatter);
    }

    vec3 shadow_factor = vec3( get_shadow_factor(screen_tex_coord, vs_output.world_pos.xyz, texture_shadow) );
    shadow_factor = max(shadow_factor, scene_sky_irradiance);

    float fresnel = clamp(0.02 + 0.98 * meanFresnel(V, N, sigmaSq), 0.0, 1.0);
    float wave_peak = pow(1.0 - vertex_normal.y, 4.0) + pow(1.0 - N.y, 2.0) * 30.0;
    wave_peak = clamp(wave_peak * simulation_amplitude, 0.0, 1.0);

    vec3 seaColor = vec3(1.0, 1.0, 1.0);
    vec3 light_color = LIGHT_COLOR.xyz * scene_sun_irradiance;

    const float foam_sharpen = 1.0;
    vec3 foam = texture(texture_foam, uv * uv_tiling + N.xz * 0.05).xyz;
    float lum = get_luminance(foam);
    foam = foam * mix(lum, clamp((lum - 1.0 + wave_peak) / wave_peak, 0.0, 1.0), foam_sharpen) * wave_peak;

    // diffuse
    vec3 diffuse_light = NdL * seaColor.xyz * (1.0 - fresnel) * light_color;

    const float specular_power = 60.0;    
    vec3 specular_lighting = vec3(pow(NdH, specular_power) * (specular_power + 2.0) / 8.0);   // specular normalization
    specular_lighting *= light_color;

    // Image based lighting
    const vec2 env_size = textureSize(texture_probe, 0);
    const float env_mipmap_count = log2(min(env_size.x, env_size.y));

    vec2 envBRDF = clamp(env_BRDF_pproximate(NdV, roughness), 0.0, 1.0);
    float shValue = fresnel * envBRDF.x + envBRDF.y;

    vec3 ibl_diffuse_color = textureLod(texture_probe, invert_y(N), env_mipmap_count - 1.0).xyz;
    vec3 ibl_specular_color = textureLod(texture_probe, invert_y(R), env_mipmap_count * roughness).xyz;

    diffuse_light += shValue * ibl_diffuse_color;
    specular_lighting += shValue * ibl_specular_color;

    // final result
    vec3 result = (foam * diffuse_light + specular_lighting) * shadow_factor + scene_in_scatter;

    float depth_diff = bg_linear_depth - scene_linear_depth;
    float opacity = pow(fresnel, 0.5) + get_luminance(specular_lighting.xyz) + depth_diff * depth_diff * 0.02;

    opacity = clamp(opacity, 0.0, 1.0) * pow(clamp(depth_diff * 0.5, 0.0, 1.0), 20.0) * distance_fade;

    fs_output.xyz = result;
    fs_output.w = clamp(opacity, 0.0, 1.0);
}
#endif
