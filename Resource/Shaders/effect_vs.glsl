#include "scene_constants.glsl"

// referene : RenderOptions.py
#define BLEND 0
#define ADDITIVE 1
#define MULTIPLY 2
#define SUBTRACT 3

uniform sampler2D texture_diffuse;
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
    vec4 prev_projection_pos;
    vec2 uv;
    vec2 next_uv;
    float sequence_ratio;
    float opacity;
};


#ifdef GL_VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
layout (location = 5) in mat4 model;
layout (location = 9) in vec4 uvs;
layout (location = 10) in vec4 sequence_opacity;


layout (location = 0) out VERTEX_OUTPUT vs_output;

void main() {
    vec4 position = vec4(0.0, 0.0, 0.0, 0.0);
    vec4 prev_position = vec4(0.0, 0.0, 0.0, 0.0);
    vec3 vertex_normal = vec3(0.0, 0.0, 0.0);
    vec3 vertex_tangent = vec3(0.0, 0.0, 0.0);

    position = vec4(vs_in_position, 1.0);
    vertex_normal = vs_in_normal;
    vertex_tangent = vs_in_tangent;
    prev_position = position;

    vertex_normal = normalize(vertex_normal);
    vertex_tangent = normalize(vertex_tangent);

    mat4 world_matrix = model * particle_matrix;

    vs_output.world_position = (world_matrix * position).xyz;
    vs_output.vertex_normal = vertex_normal;
    vs_output.vertex_color = vs_in_color;

    vec3 bitangent = cross(vertex_tangent, vertex_normal);

    // Note : Normalization is very important because tangent_to_world may have been scaled..
    vs_output.tangent_to_world = world_matrix *
        mat4(vec4(vertex_tangent, 0.0), vec4(vertex_normal, 0.0), vec4(bitangent, 0.0), vec4(0.0, 0.0, 0.0, 1.0));

    position = VIEW_PROJECTION * world_matrix * position;
    prev_position = PREV_VIEW_PROJECTION * world_matrix * prev_position;

    vs_output.projection_pos = position;
    vs_output.prev_projection_pos = prev_position;
    vec2 uv_size = vec2(sequence_width, sequence_height) * vs_in_tex_coord.xy;
    vs_output.uv = uvs.xy + uv_size;
    vs_output.next_uv = uvs.zw + uv_size;
    vs_output.sequence_ratio = sequence_opacity.x;
    vs_output.opacity = sequence_opacity.y;

    gl_Position = position;
}
#endif