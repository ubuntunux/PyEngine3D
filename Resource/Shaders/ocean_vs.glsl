#include "scene_constants.glsl"
#include "utility.glsl"

#ifdef MATERIAL_COMPONENTS
    uniform sampler2D texture_noise;
#endif

uniform float height;
uniform vec2 grid_size;

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
};

#ifdef GL_VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
layout (location = 5) in vec2 offset;   // instance buffer

layout (location = 0) out VERTEX_OUTPUT vs_output;


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

    vec2 uv = world_pos.xz * 0.001;
    float noise = texture(texture_noise, uv + vec2(TIME) * 0.001).x;
    world_pos.y += sin(TIME + noise * 30.0) * 2.7;

    vec4 proj_pos = VIEW_PROJECTION * vec4(world_pos.xyz, 1.0);
    if(dist < NEAR_FAR.y)
    {
        proj_pos.xy = mix(proj_pos.xy, vs_in_position.xz * proj_pos.w, clamp(abs(vs_in_position.xz) * 10.0 - 9.0, 0.0, 1.0));
    }

    /*
    // Instanced Grid
    vec3 world_pos = vec3(0.0);
    world_pos.xz += (vs_in_position.xz + offset) * grid_size;
    world_pos.y += height;

    vec2 uv = world_pos.xz * 0.01;
    float noise = texture(texture_noise, uv + vec2(TIME) * 0.001).x;
    world_pos.y += sin(TIME + noise * 30.0) * 0.7;

    vec4 proj_pos = VIEW_PROJECTION * vec4(world_pos.xyz, 1.0);
    */

    vs_output.position = world_pos.xyz;
    vs_output.tex_coord = uv;
    gl_Position = proj_pos;
}
#endif // GL_VERTEX_SHADER