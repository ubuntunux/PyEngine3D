#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"

uniform float tessellation_level;
uniform mat4 model;
uniform sampler2D texture_height_map;


#ifdef VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;

out block
{
    vec3 world_position;
    vec3 vertex_normal;
    vec2 tex_coord;
} vs_output;

void main()
{
    vec4 position = vec4(vs_in_position, 1.0);

    position.y += texture2DLod(texture_height_map, vs_in_tex_coord, 0.0).x;

    vec3 vertex_normal = normalize(vs_in_normal);
    vec3 world_position = (model * position).xyz;

    vs_output.world_position = world_position;
    vs_output.vertex_normal = vertex_normal;
    vs_output.tex_coord = vs_in_tex_coord;

    gl_Position = VIEW_PROJECTION * vec4(world_position, 1.0);
}
#endif

/*
#ifdef TESS_CONTROL_SHADER
layout (vertices = 4) out;

in block
{
    vec3 world_position;
    vec3 vertex_normal;
    vec2 tex_coord;
} vs_output[];

out block
{
    vec3 world_position;
    vec3 vertex_normal;
    vec2 tex_coord;
} ts_output[];


void main()
{
    if(gl_InvocationID == 0)
    {
        gl_TessLevelInner[0] = tessellation_level;
        gl_TessLevelInner[1] = tessellation_level;
        gl_TessLevelOuter[0] = tessellation_level;
        gl_TessLevelOuter[1] = tessellation_level;
        gl_TessLevelOuter[2] = tessellation_level;
        gl_TessLevelOuter[3] = tessellation_level;
    }

    ts_output[gl_InvocationID].world_position = vs_output[gl_InvocationID].world_position;
    ts_output[gl_InvocationID].vertex_normal = vs_output[gl_InvocationID].vertex_normal;
    ts_output[gl_InvocationID].tex_coord = vs_output[gl_InvocationID].tex_coord;
    gl_out[gl_InvocationID].gl_Position = gl_in[gl_InvocationID].gl_Position;
}
#endif


#ifdef TESS_EVALUATION_SHADER
layout(quads, equal_spacing, ccw) in;

in block
{
    vec3 world_position;
    vec3 vertex_normal;
    vec2 tex_coord;
} ts_output[];

out block
{
    vec3 world_position;
    vec3 vertex_normal;
    vec2 tex_coord;
} te_output;

void main()
{
    te_output.world_position = mix(mix(ts_output[0].world_position, ts_output[3].world_position, gl_TessCoord.x),
                                   mix(ts_output[1].world_position, ts_output[2].world_position, gl_TessCoord.x),
                                   gl_TessCoord.y);
    te_output.vertex_normal = mix(mix(ts_output[0].vertex_normal, ts_output[3].vertex_normal, gl_TessCoord.x),
                                   mix(ts_output[1].vertex_normal, ts_output[2].vertex_normal, gl_TessCoord.x),
                                   gl_TessCoord.y);
    te_output.tex_coord = mix(mix(ts_output[0].tex_coord, ts_output[3].tex_coord, gl_TessCoord.x),
                                   mix(ts_output[1].tex_coord, ts_output[2].tex_coord, gl_TessCoord.x),
                                   gl_TessCoord.y);
    gl_Position = VIEW_PROJECTION * vec4(te_output.world_position, 1.0);
}
#endif
*/

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
