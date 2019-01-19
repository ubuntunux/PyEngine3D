#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"

uniform vec2 height_map_size;
uniform float tessellation_level;
uniform mat4 model;
uniform sampler2D texture_height_map;


#ifdef VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
// instance data
layout (location = 5) in vec4 vs_in_isntance_offset;

out block
{
    vec3 world_position;
    vec3 vertex_normal;
    vec2 tex_coord;
} vs_output;

void main()
{
    vec4 position = vec4(vs_in_position, 1.0);
    position.xz += vs_in_isntance_offset.xy * 2.0;

    vec2 tex_coord = position.xz / height_map_size;
    position.y += texture2DLod(texture_height_map, tex_coord, 0.0).x;

    vec3 vertex_normal = normalize(vs_in_normal);
    vec3 world_position = (model * position).xyz;

    vs_output.world_position = world_position;
    vs_output.vertex_normal = vertex_normal;
    vs_output.tex_coord = tex_coord;

    gl_Position = VIEW_PROJECTION * vec4(world_position, 1.0);
}
#endif


#ifdef FRAGMENT_SHADER
in block
{
    vec3 world_position;
    vec3 vertex_normal;
    vec2 tex_coord;
} te_output;

layout (location = 0) out vec4 fs_diffuse;
layout (location = 1) out vec4 fs_material;
layout (location = 2) out vec4 fs_normal;

void main()
{
    float emissive = 0.0;
    float roughness = 1.0;
    float metalicness = 0.0;
    float reflectance = 0.0;

    fs_diffuse.xyz = pow(texture2D(texture_height_map, te_output.tex_coord).xyz, vec3(2.2));
    fs_diffuse.w = emissive;

    fs_material = vec4(roughness, metalicness, reflectance, 0.0);
    fs_normal = vec4(0.0, 1.0, 0.0, 0.0);
}
#endif
