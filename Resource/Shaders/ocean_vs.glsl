#include "scene_constants.glsl"
#include "utility.glsl"

uniform float height;
uniform vec2 grid_size;

#ifdef MATERIAL_COMPONENTS
    uniform vec2 uv_tiling;
    uniform sampler2D texture_noise;
    uniform sampler2D texture_foam;
#endif

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 wave_offset;
};

#ifdef GL_VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
layout (location = 5) in vec2 offset;   // instance buffer

layout (location = 0) out VERTEX_OUTPUT vs_output;

vec3 GerstnerWave(vec3 world_pos, vec3 dir, float frequency, float speed, float intensity, float noise)
{
    speed *= TIME * frequency;
    dir = normalize(dir);

    float noise_offset = noise * 5.0;
    intensity = intensity * (noise * 0.5 + 0.5);

    float d = dot(dir, world_pos) * frequency + noise_offset;
    float s = sin(d + speed) * intensity;
    float c = cos(d + speed) * intensity;
    return vec3(0.0, c, 0.0) - dir * s * 2.0;
}


void main()
{
    // Projected Grid Ocean
    float h = height - CAMERA_POSITION.y;

    vec4 world_pos = INV_VIEW_ORIGIN * INV_PROJECTION * vec4(vs_in_position.xz + JITTER_OFFSET, -1.0, 1.0);
    world_pos.xyz /= world_pos.w;

    vec3 dir = normalize(world_pos.xyz);
    float dist;
    if(0.0 < h)
    {
        dist = (0.0 < dir.y) ? (h / dir.y) : NEAR_FAR.y;
    }
    else
    {
        dist = (dir.y < 0.0) ? (h / dir.y) : NEAR_FAR.y;
    }

    world_pos.xz = dir.xz * dist;
    world_pos.y = h;
    world_pos.xyz += CAMERA_POSITION.xyz;

    vec2 uv = world_pos.xz * 0.01;
    float noise = texture(texture_noise, uv * 0.5).x * 0.0;

    vec3 wave_offset = GerstnerWave(world_pos.xyz, vec3(1.0, 0.0, 1.0), 0.05, 15.0, 8.0, noise);
    wave_offset += GerstnerWave(world_pos.xyz, vec3(-0.2, 0.0, 1.0), 0.07, 10.5, 7.0, noise);
    wave_offset += GerstnerWave(world_pos.xyz, vec3(0.5, 0.0, 1.0), 0.09, 18.71, 5.0, noise);
    wave_offset += GerstnerWave(world_pos.xyz, vec3(0.7, 0.0, -0.2), 0.06, 12.31, 5.0, noise);

    //wave_offset += GerstnerWave(world_pos.xyz, vec3(0.1, 0.0, 0.19), 0.432, 5.31, 1.0, noise);
    //wave_offset += GerstnerWave(world_pos.xyz, vec3(-0.31, 0.0, -2.35), 0.65, 2.31, 0.3, noise);

    world_pos.xyz += wave_offset;

    vec4 proj_pos = VIEW_PROJECTION * vec4(world_pos.xyz, 1.0);
    if(dist < NEAR_FAR.y)
    {
        proj_pos.xy = mix(proj_pos.xy, vs_in_position.xz * proj_pos.w, clamp(abs(vs_in_position.xz) * 10.0 - 9.0, 0.0, 1.0));
    }

    vs_output.wave_offset = wave_offset;
    vs_output.tex_coord = uv;
    gl_Position = proj_pos;
}
#endif // GL_VERTEX_SHADER