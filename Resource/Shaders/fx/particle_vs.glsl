#include "scene_constants.glsl"

uniform sampler2D texture_diffuse;

uniform bool billboard;
uniform vec3 color;
uniform int blend_mode;
uniform mat4 particle_matrix;
uniform float sequence_width;
uniform float sequence_height;


struct VERTEX_OUTPUT
{
    vec3 world_position;
    vec3 vertex_normal;
    vec4 vertex_color;
    mat4 tangent_to_world;
    vec4 projection_pos;
    vec2 uv;
    vec2 next_uv;
    float sequence_ratio;
    float opacity;
};


#ifdef VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
layout (location = 5) in mat4 parent_matrix;
layout (location = 9) in mat4 local_matrix;
layout (location = 13) in vec4 uvs;
layout (location = 14) in vec4 sequence_opacity;


layout (location = 0) out VERTEX_OUTPUT vs_output;

void main() {
    vec3 vertex_normal = normalize(vs_in_normal);
    vec3 vertex_tangent = normalize(vs_in_tangent);
    vec4 vertex_position = vec4(vs_in_position, 1.0);
    mat4 world_matrix;
    vec3 world_position;

    if(EMITTER_BILLBOARD)
    {
        world_matrix = local_matrix;
        world_matrix[3].xyz = vec3(0.0);
        world_matrix = INV_VIEW_ORIGIN * world_matrix;

        vec3 local_position = (parent_matrix * local_matrix)[3].xyz;
        world_position = local_position + (world_matrix * vertex_position).xyz;
    }
    else
    {
        world_matrix = parent_matrix * local_matrix;
        world_position = (world_matrix * vertex_position).xyz;
    }

    vs_output.world_position = world_position.xyz;
    vs_output.vertex_normal = vertex_normal;
    vs_output.vertex_color = vs_in_color;

    vec3 bitangent = cross(vertex_tangent, vertex_normal);

    // Note : Normalization is very important because tangent_to_world may have been scaled..
    vs_output.tangent_to_world = world_matrix *
        mat4(vec4(vertex_tangent, 0.0), vec4(vertex_normal, 0.0), vec4(bitangent, 0.0), vec4(0.0, 0.0, 0.0, 1.0));

    vs_output.projection_pos = VIEW_PROJECTION * vec4(world_position, 1.0);
    vec2 uv_size = vs_in_tex_coord.xy / vec2(EMITTER_CELL_COUNT);
    vs_output.uv = uvs.xy + uv_size;
    vs_output.next_uv = uvs.zw + uv_size;
    vs_output.sequence_ratio = sequence_opacity.x;
    vs_output.opacity = sequence_opacity.y;

    gl_Position = vs_output.projection_pos;
}
#endif