#include "scene_constants.glsl"
#include "utility.glsl"

#ifdef MATERIAL_COMPONENTS
    uniform sampler2D texture_noise;
#endif

uniform float height;


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

layout (location = 0) out VERTEX_OUTPUT vs_output;


void main()
{
    float h = height - CAMERA_POSITION.y;

    vec4 relarive_pos = INV_VIEW_ORIGIN * INV_PROJECTION * vec4(vs_in_position.xy + JITTER_OFFSET, -1.0, 1.0);
    relarive_pos.xyz /= relarive_pos.w;

    vec3 dir = normalize(relarive_pos.xyz);

    float dist;

    if(0.0 < h)
    {
        dist = (0.0 < dir.y) ? (h / dir.y) : NEAR_FAR.y;
    }
    else
    {
        dist = (dir.y < 0.0) ? (h / dir.y) : NEAR_FAR.y;
    }

    relarive_pos.xz = dir.xz * dist;
    relarive_pos.y = h;

    vec3 world_pos = relarive_pos.xyz + CAMERA_POSITION.xyz;
    vec2 uv = world_pos.xz * 0.01;
    float noise = texture(texture_noise, uv).x;

    world_pos.y += sin(TIME + noise * 10.0) * 2.0;

    vs_output.position = world_pos.xyz;
    vs_output.tex_coord = vs_output.position.xz * 0.01;

    vec4 proj_pos = VIEW_PROJECTION * vec4(world_pos.xyz, 1.0);
    proj_pos.x = vs_in_position.x * proj_pos.w;

    gl_Position = proj_pos;
}
#endif // GL_VERTEX_SHADER