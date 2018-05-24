#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"

uniform float height;
uniform float simulation_amplitude;
uniform vec4 simulation_size;
uniform vec2 cell_size;

uniform sampler2DArray fftWavesSampler;
uniform sampler3D slopeVarianceSampler;
uniform sampler2D texture_scene;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_shadow;
uniform samplerCube texture_probe;

#ifdef MATERIAL_COMPONENTS
    uniform vec2 uv_tiling;
    uniform sampler2D texture_foam;
#endif


struct VERTEX_OUTPUT
{
    vec4 uvs;
    float linear_depth;
    vec3 wave_offset;
    float shadow_factor;
    vec3 vertex_normal;
    vec3 relative_pos;
    vec4 proj_pos;
    vec3 sun_irradiance;
    vec3 sky_irradiance;
};

#ifdef GL_VERTEX_SHADER
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

    return CAMERA_POSITION.xyz + dist * worldDir + vec3(0.0, height, 0.0);
}

void main()
{
    vec3 vertex_scale = vec3(1.5, 1.5, 1.0);
    vec4 vertex_pos = vec4(vs_in_position * vertex_scale, 1.0);
    vec3 world_pos = oceanWorldPos(vertex_pos);
    vec3 relative_pos = world_pos - CAMERA_POSITION.xyz;
    float dist_xz = length(relative_pos.xz);
    float dist = length(relative_pos);
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
    if(dist_xz < NEAR_FAR.y)
    {
        fade = 1.0 - pow(clamp(length(vertex_pos.xy / vertex_scale.xy), 0.0, 1.0), 4.0);
        proj_pos.xy = mix(vertex_pos.xy * proj_pos.w, proj_pos.xy, fade);
    }

    vec2 screen_coord = (proj_pos.xy / proj_pos.w) * 0.5 + 0.5;

    float shadow_factor = get_shadow_factor(screen_coord, world_pos, texture_shadow);

    vec3 in_scatter;
    vec3 sun_irradiance;
    vec3 sky_irradiance;
    GetSceneRadiance(ATMOSPHERE, dist, eye_direction, vertex_normal, sun_irradiance, sky_irradiance, in_scatter);

    vs_output.sun_irradiance = sun_irradiance;
    vs_output.sky_irradiance = sky_irradiance;

    vs_output.uvs.xy = u;
    vs_output.uvs.zw = world_pos.xz;
    vs_output.shadow_factor = shadow_factor;
    vs_output.wave_offset = dP;
    vs_output.vertex_normal = vertex_normal;
    vs_output.relative_pos = relative_pos;
    vs_output.linear_depth = dot(relative_pos, vec3(VIEW_ORIGIN[0].z, VIEW_ORIGIN[1].z, VIEW_ORIGIN[2].z));
    vs_output.proj_pos = proj_pos;
    gl_Position = proj_pos;
}
#endif


#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;


void main()
{
    vec2 uv = vs_output.uvs.xy;
    vec2 fft_uv = vs_output.uvs.zw;
    vec2 screen_tex_coord = (vs_output.proj_pos.xy / vs_output.proj_pos.w) * 0.5 + 0.5;
    vec3 relative_pos = vs_output.relative_pos;
    vec3 world_pos = relative_pos + CAMERA_POSITION.xyz;
    float linear_depth = vs_output.linear_depth;
    float depth = linear_depth_to_depth(linear_depth);
    float scene_linear_depth = texture2D(texture_linear_depth, screen_tex_coord).x;
    vec3 sun_irradiance = vs_output.sun_irradiance;
    vec3 sky_irradiance = vs_output.sky_irradiance;
    float shadow_factor = vs_output.shadow_factor;

    vec2 slopes = texture2DArrayLod(fftWavesSampler, vec3(uv / simulation_size.x, 1.0), 0.0).xy;
    slopes += texture2DArrayLod(fftWavesSampler, vec3(uv / simulation_size.y, 1.0), 0.0).zw;
    slopes += texture2DArrayLod(fftWavesSampler, vec3(uv / simulation_size.z, 2.0), 0.0).xy;
    slopes += texture2DArrayLod(fftWavesSampler, vec3(uv / simulation_size.w, 2.0), 0.0).zw;

    float dist = length(relative_pos);
    vec3 V = -relative_pos / dist;

    vec3 vertex_normal = normalize(vs_output.vertex_normal);
    vec3 N = normalize(vec3(-slopes.x, 1.0, -slopes.y) + vertex_normal * 0.5);
    vec3 smooth_normal = normalize(vec3(-slopes.x, 1.0, -slopes.y) + vertex_normal * 2.0);

    vec3 L = LIGHT_DIRECTION.xyz;
    vec3 H = normalize(V + L);
    vec3 R = reflect(-V, smooth_normal);

    float NdL = max(0.0, dot(N, L));
    float NdV = max(0.0, dot(smooth_normal, V));
    float NdH = max(0.0, dot(N, H));
    float HdV = max(0.0, dot(H, V));
    float LdV = max(0.0, dot(L, V));

    vec3 light_color = LIGHT_COLOR.xyz * (sun_irradiance + sky_irradiance);
    vec3 seaColor = vec3(1.0, 1.0, 1.0);
    vec3 scene_reflect_color = textureCubeLod(texture_probe, invert_y(R), 0.0).xyz;

    vec3 F0 = vec3(0.04);
    vec3 fresnel = fresnelSchlick(NdV, F0);

    fs_output.xyz = mix(NdL * light_color, scene_reflect_color, fresnel) * shadow_factor;
    fs_output.w = 1.0;
}
#endif
