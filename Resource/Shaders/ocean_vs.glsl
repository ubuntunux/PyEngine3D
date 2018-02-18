#include "scene_constants.glsl"
#include "utility.glsl"

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
};

uniform float height;

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

    vec3 world_pos;

    float radius = max(abs(vs_in_position.x), abs(vs_in_position.y));

    if(radius == 0.0)
    {
        world_pos.xz = vec2(0.0);
    }
    else
    {
        world_pos.xz = normalize(vs_in_position.yx) * radius * NEAR_FAR.y;
    }

    world_pos.y = h;
    vec4 proj_pos = PROJECTION * VIEW_ORIGIN * vec4(world_pos.xyz, 1.0);

    /*vec4 world_pos = INV_VIEW_ORIGIN * INV_PROJECTION * vec4(vs_in_position.xy, -1.0, 1.0);
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

    vs_output.tex_coord = vs_in_tex_coord;
    vs_output.position = world_pos.xyz;

    vec4 proj_pos = PROJECTION * VIEW_ORIGIN * vec4(world_pos.xyz, 1.0);
    proj_pos.x = vs_in_position.x * proj_pos.w;*/

    vs_output.tex_coord = vs_in_tex_coord;
    vs_output.position = vs_in_position;

    gl_Position = proj_pos;
}
#endif // GL_VERTEX_SHADER