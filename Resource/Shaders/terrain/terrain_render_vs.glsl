#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"

uniform vec2 height_map_size;
uniform vec3 scale;
uniform float subdivide_level;
uniform mat4 model;
uniform sampler2D texture_height_map;

struct VERTEX_OUTPUT
{
    vec3 world_position;
    vec3 vertex_normal;
    vec2 tex_coord;
};


#ifdef VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
// instance data
layout (location = 5) in vec4 vs_in_isntance_offset;

layout (location = 0) out VERTEX_OUTPUT vs_output;

void main()
{
    vec4 position = vec4(vs_in_position, 1.0);
    position.xz = position.xz * 0.5 + 0.5;
    position.xz += vs_in_isntance_offset.xy;

    vec2 tex_coord = position.xz / height_map_size;
    float height = texture2DLod(texture_height_map, tex_coord, 0.0).x;
    position.y += height;

    vec2 tex_coord_delta = 1.0 / (height_map_size * subdivide_level);
    vec3 size_of_grid = vec3(scale.x / subdivide_level, scale.y, scale.z / subdivide_level);

    float height_w = texture2DLod(texture_height_map, tex_coord + vec2(tex_coord_delta.x, 0.0), 0.0).x;
    float height_h = texture2DLod(texture_height_map, tex_coord + vec2(0.0, tex_coord_delta.y), 0.0).x;

    vec3 vector_w = normalize(vec3(size_of_grid.x, size_of_grid.y * (height_w - height), 0.0));
    vec3 vector_h = normalize(vec3(0.0, size_of_grid.y * (height_h - height), size_of_grid.z));

    vec3 vertex_normal = cross(vector_h, vector_w);
    vec3 world_position = (model * position).xyz;

    vs_output.world_position = world_position;
    vs_output.vertex_normal = vertex_normal;
    vs_output.tex_coord = tex_coord;

    gl_Position = VIEW_PROJECTION * vec4(world_position, 1.0);
}
#endif