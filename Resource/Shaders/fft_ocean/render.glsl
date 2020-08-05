#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"

uniform float height;
uniform float simulation_wind;
uniform float simulation_amplitude;
uniform vec4 simulation_size;
uniform vec2 cell_size;
uniform float t;

uniform sampler2DArray fftWavesSampler;
uniform sampler3D slopeVarianceSampler;
uniform sampler2D texture_scene;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_shadow;
uniform samplerCube texture_probe;

uniform sampler2D texture_noise;
uniform sampler2D texture_caustic;
uniform sampler2D texture_foam;


struct VERTEX_OUTPUT
{
    vec4 uvs;
    vec3 wave_offset;
    float shadow_factor;
    float vertex_noise;
    float screen_fade;
    vec3 vertex_normal;
    vec3 relative_pos;
    vec4 proj_pos;
    vec3 sun_irradiance;
    vec3 sky_irradiance;
};

#ifdef VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
layout (location = 5) in vec2 offset;   // instance buffer

layout (location = 0) out VERTEX_OUTPUT vs_output;


vec3 oceanWorldPos(vec4 vertex)
{
    float height_diff = height - CAMERA_POSITION.y;
    vec3 cameraDir = normalize((INV_PROJECTION * (vertex + vec4(JITTER_OFFSET, 0.0, 0.0))).xyz);
    vec3 worldDir = (INV_VIEW_ORIGIN * vec4(cameraDir, 0.0)).xyz;
    const float far_dist = NEAR_FAR.y * 2.0;

    float dist = 0.0;

    if(0.0 < height_diff)
    {
        dist = (0.0 < worldDir.y) ? (height_diff / worldDir.y) : far_dist;
    }
    else
    {
        dist = (worldDir.y < 0.0) ? (height_diff / worldDir.y) : far_dist;
    }

    dist = min(far_dist, dist);

    vec3 world_pos = vec3(0.0, height, 0.0);
    world_pos.xz += CAMERA_POSITION.xz + dist * worldDir.xz;
    return world_pos;
}

void main()
{
    vec3 vertex_scale = vec3(1.5, 1.5, 1.0);
    vec4 vertex_pos = vec4(vs_in_position * vertex_scale, 1.0);
    vec3 world_pos = oceanWorldPos(vertex_pos);
    vec3 relative_pos = world_pos - CAMERA_POSITION.xyz;
    float dist_xz = length(relative_pos.xz);
    float dist = length(relative_pos);

    float screen_fade = 1.0f - saturate(ceil(max(abs(vs_in_position.x), abs(vs_in_position.y)) - 0.999f));

    vec2 u = world_pos.xz;
    vec2 ux = oceanWorldPos(vertex_pos + vec4(cell_size.x, 0.0, 0.0, 0.0)).xz;
    vec2 uy = oceanWorldPos(vertex_pos + vec4(0.0, cell_size.y, 0.0, 0.0)).xz;
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

    vec3 vertex_normal = vec3(-dP.x, dP.y * 0.5 + 0.5, -dP.z);
    vertex_normal = safe_normalize(mix(vec3(0.0, 1.0, 0.0), vertex_normal, saturate(simulation_amplitude)));

    world_pos += dP * simulation_amplitude;
    relative_pos = world_pos - CAMERA_POSITION.xyz;

    vec3 eye_direction = normalize(relative_pos);
    vec4 proj_pos = VIEW_PROJECTION * vec4(world_pos.xyz, 1.0);

    float fade = 1.0f;
    if(dist_xz < NEAR_FAR.y && vs_in_position.y < 0.0)
    {
        proj_pos.xy = mix(vs_in_position.xy * proj_pos.w, proj_pos.xy, screen_fade);
    }

    vec2 screen_coord = (proj_pos.xy / proj_pos.w) * 0.5 + 0.5;

    float vertex_noise = texture2DLod(texture_noise, world_pos.xz * 0.005, 0.0).x;
    float shadow_factor = get_shadow_factor(world_pos, dot(LIGHT_DIRECTION.xyz, vertex_normal.xyz), texture_shadow);

    vec3 in_scatter;
    vec3 sun_irradiance;
    vec3 sky_irradiance;
    GetSceneRadiance(ATMOSPHERE, dist * 0.1, eye_direction, vertex_normal, sun_irradiance, sky_irradiance, in_scatter);

    vs_output.sun_irradiance = sun_irradiance;
    vs_output.sky_irradiance = sky_irradiance;

    vs_output.uvs.xy = u;
    vs_output.uvs.zw = world_pos.xz;
    vs_output.shadow_factor = shadow_factor;
    vs_output.vertex_noise = vertex_noise;
    vs_output.screen_fade = screen_fade;
    vs_output.wave_offset = dP;
    vs_output.vertex_normal = vertex_normal;
    vs_output.relative_pos = relative_pos;
    vs_output.proj_pos = proj_pos;
    gl_Position = proj_pos;
}
#endif


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;


void main()
{
    vec2 uv = vs_output.uvs.xy;
    vec2 fft_uv = vs_output.uvs.zw;
    vec2 screen_tex_coord = (vs_output.proj_pos.xy / vs_output.proj_pos.w) * 0.5 + 0.5;
    vec3 view_center_ray = vec3(VIEW_ORIGIN[0].z, VIEW_ORIGIN[1].z, VIEW_ORIGIN[2].z);
    float screen_fade = pow(vs_output.screen_fade, 100.0f);

    vec3 relative_pos = vs_output.relative_pos;
    vec3 world_pos = relative_pos + CAMERA_POSITION.xyz;
    float dist = length(relative_pos);
    vec3 V = -relative_pos / dist;
    float view_ray_angle = dot(view_center_ray, V);

    float scene_dist = texture2D(texture_linear_depth, screen_tex_coord).x / view_ray_angle;
    float vertex_noise = vs_output.vertex_noise;

    // fix scene_depth
    vec3 tempPos = -V * scene_dist;
    tempPos.xz = mix(relative_pos.xz, tempPos.xz, abs(V.y));
    scene_dist = length(tempPos.xyz);

    vec3 sun_irradiance = vs_output.sun_irradiance;
    vec3 sky_irradiance = vs_output.sky_irradiance;
    vec3 shadow_factor = max(sky_irradiance, vec3(vs_output.shadow_factor));

    vec2 slopes = texture2DArrayLod(fftWavesSampler, vec3(uv / simulation_size.x, 1.0), 0.0).xy;
    slopes += texture2DArrayLod(fftWavesSampler, vec3(uv / simulation_size.y, 1.0), 0.0).zw;
    slopes += texture2DArrayLod(fftWavesSampler, vec3(uv / simulation_size.z, 2.0), 0.0).xy;
    slopes += texture2DArrayLod(fftWavesSampler, vec3(uv / simulation_size.w, 2.0), 0.0).zw;

    vec3 vertex_normal = normalize(vs_output.vertex_normal);
    vec3 N = normalize(vec3(-slopes.x, 1.0, -slopes.y) + vertex_normal * 0.2);
    vec3 smooth_normal = normalize(vec3(-slopes.x, 1.0, -slopes.y) + vertex_normal * 0.5);

    vec3 L = LIGHT_DIRECTION.xyz;
    vec3 H = normalize(V + L);

    float NdL = max(0.0, dot(N, L));
    float NdV = max(0.0, dot(N, V));
    float NdH = max(0.0, dot(N, H));
    float HdV = max(0.0, dot(H, V));
    float LdV = max(0.0, dot(L, V));

    vec3 F0 = vec3(0.04);
    float fresnel = fresnelSchlick(max(0.2, dot(smooth_normal, V)), F0).x;

    // refract
    vec2 reflected_screen_uv = screen_tex_coord + N.xz * 0.05f;
    float refracted_scene_dist = texture2D(texture_linear_depth, reflected_screen_uv).x / view_ray_angle;
    float refracted_scene_dist_origin = refracted_scene_dist;

    // fix refractedSceneDepth
    tempPos = -V * refracted_scene_dist;
    tempPos.xz = mix(relative_pos.xz, tempPos.xz, abs(V.y));
    refracted_scene_dist = length(tempPos.xyz);

    float dist_diff = max(0.0f, max(scene_dist, refracted_scene_dist) - dist);

    // groud pos
    vec3 groundPos = world_pos - V * dist_diff + vec3(N.x, 0.0f, N.z) * 0.5f;

    bool isUnderWater = CAMERA_POSITION.y < height;
    float opacity = pow(saturate(dist_diff * 0.3), 1.0) * screen_fade;
    float inv_opacity = 1.0f - opacity;

    vec3 light_color = LIGHT_COLOR.xyz * sun_irradiance;

    // Water Base Color
    vec3 sea_color_near = vec3(198.0, 230.0, 213.0) / 255.0;
    vec3 sea_color_mid = vec3(121.0, 176.0, 188.0) / 255.0;
    vec3 sea_color_far = vec3(58.0, 47.0, 99.0) / 255.0;
    vec3 water_color;
    {
        water_color = mix(sea_color_near, sea_color_mid, sqrt(saturate(dist * 0.5)));
        water_color = mix(water_color, sea_color_far, sqrt(saturate(dist * 0.05)));
        water_color = pow(water_color, vec3(2.2));
    }

    // Reflection
    vec3 R = reflect(-V, smooth_normal);
    vec3 scene_reflect_color = textureCubeLod(texture_probe, invert_y(R), 0.0).xyz;

    // Under Water
    vec3 under_water_color = texture2DLod(texture_scene, (refracted_scene_dist <= dist) ? screen_tex_coord : reflected_screen_uv, 0.0).xyz;
    {
        // Under Water Caustic
        if(false == isUnderWater)
        {
            const bool isSimpleShadow = true;
            vec3 under_water_shadow = vec3(get_shadow_factor(world_pos, dot(L, vertex_normal.xyz), texture_shadow, isSimpleShadow));
            under_water_shadow = max(sky_irradiance, under_water_shadow);

            const float chromaSeperation = sin(t * 3.5f) * 0.005;
            vec2 caustic_uv = (groundPos + L * dist_diff).xz * 0.3 + vertex_normal.xz * 0.5;

            vec3 caustic_color;
            caustic_color.r = texture2D(texture_caustic, caustic_uv + vec2(0.0f, chromaSeperation)).r;
            caustic_color.g = texture2D(texture_caustic, caustic_uv + vec2(chromaSeperation, 0.0f)).g;
            caustic_color.b = texture2D(texture_caustic, caustic_uv - vec2(chromaSeperation, chromaSeperation)).b;
            caustic_color *= under_water_shadow * sun_irradiance * screen_fade * saturate(dist_diff) * 2.0;

            // apply caustic
            under_water_color += caustic_color;
        }

        float fog_ratio = saturate(abs(refracted_scene_dist_origin) * 0.05f);
        vec3 fog_color = mix(under_water_color, sea_color_far, fog_ratio * fog_ratio);

        under_water_color = mix(under_water_color, water_color * under_water_color, opacity);
        under_water_color = mix(fog_color, under_water_color, screen_fade) * inv_opacity;
    }

    // White cap
    float wave_peak = pow(saturate((vs_output.wave_offset.y * 0.5 + 0.5) * 1.7 + saturate(1.0f - N.y) * 2.0), 12.0f);
    float white_cap = saturate(wave_peak * simulation_wind);

    // Transmission
    float transmission = wave_peak * 2.0;

    // Foam
    vec3 foam = vec3(0.0);
    {
        foam = pow(texture2D(texture_foam, uv * 0.3 + vertex_noise * 0.2).xyz, vec3(2.2));
        foam += pow(texture2D(texture_foam, uv * -0.05 + vertex_noise * 0.3).xyz, vec3(2.2));
        foam *= 0.5;

        float foam_amount = saturate(inv_opacity * saturate(dist_diff) + white_cap * 1.0);
        float sharpen = mix(0.6, 0.1, foam_amount);
        foam = mix(vec3(0.0), foam, saturate((foam.x - sharpen) / (1.0f - sharpen) * 3.0f)) * foam_amount;
    }

    // Specular
    vec3 light_fresnel = fresnelSchlick(HdV, F0);
    float roughness = 0.1;
    float specular_light = cooktorrance_specular(light_fresnel, NdL, NdV, NdH, roughness).x * 2.0;

    // scattering
    vec3 scattering_normal = normalize(vec3(vertex_normal.x, 5.0, vertex_normal.z));
    float scattering = pow(abs(dot(H, scattering_normal)), 20.0) * (0.5 - dot(scattering_normal, V) * 0.5);
    specular_light += scattering;
    transmission += scattering * 10.0;

    float foam_lum = dot(vec3(0.3f, 0.59f, 0.11f), foam);
    specular_light *= saturate(1.0f - foam_lum * 2.0f);
    fresnel *= saturate(1.0f - foam_lum * 2.0f);

    vec3 diffuse_lighting = max(sky_irradiance, vec3(dot(N, L) * 0.5 + 0.5));

    fs_output.xyz = (mix(water_color, scene_reflect_color, fresnel) + foam) * diffuse_lighting + specular_light;
    fs_output.xyz += transmission * water_color;
    fs_output.xyz *= light_color * shadow_factor;

    // final output
    opacity = saturate(opacity + (foam_lum + specular_light + fresnel + transmission * 0.01f)) * saturate(dist_diff);
    fs_output.xyz = mix(under_water_color.xyz, fs_output.xyz, opacity * screen_fade);
    fs_output.w = 1.0;
}
#endif
