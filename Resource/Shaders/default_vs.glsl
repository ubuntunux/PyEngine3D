#define SKELETAL 0

#include "scene_constants.glsl"
#include "default_material.glsl"

uniform bool is_instancing;
uniform mat4 model;

#if 1 == SKELETAL
uniform mat4 bone_matrices[MAX_BONES];
uniform mat4 prev_bone_matrices[MAX_BONES];
#endif

struct VERTEX_OUTPUT
{
    vec3 world_position;
    vec3 vertex_normal;
    vec4 vertex_color;
    vec2 tex_coord;
    mat4 tangent_to_world;
    vec4 projection_pos;
    vec4 prev_projection_pos;
};

//----------- VERTEX_SHADER ---------------//

#ifdef VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
#if 1 == SKELETAL
layout (location = 5) in vec4 vs_in_bone_indicies;
layout (location = 6) in vec4 vs_in_bone_weights;
#endif
layout (location = 7) in mat4 vs_in_isntance_matrix;

layout (location = 0) out VERTEX_OUTPUT vs_output;

void main() {
    vec4 position = vec4(0.0, 0.0, 0.0, 0.0);
    vec4 prev_position = vec4(0.0, 0.0, 0.0, 0.0);
    vec3 vertex_normal = vec3(0.0, 0.0, 0.0);
    vec3 vertex_tangent = vec3(0.0, 0.0, 0.0);

#if 1 == SKELETAL
    for(int i=0; i<MAX_BONES_PER_VERTEX; ++i)
    {
        prev_position += (prev_bone_matrices[int(vs_in_bone_indicies[i])] * vec4(vs_in_position, 1.0)) * vs_in_bone_weights[i];
        position += (bone_matrices[int(vs_in_bone_indicies[i])] * vec4(vs_in_position, 1.0)) * vs_in_bone_weights[i];
        vertex_normal += (bone_matrices[int(vs_in_bone_indicies[i])] * vec4(vs_in_normal, 0.0)).xyz * vs_in_bone_weights[i];
        vertex_tangent += (bone_matrices[int(vs_in_bone_indicies[i])] * vec4(vs_in_tangent, 0.0)).xyz * vs_in_bone_weights[i];
    }
    position /= position.w;
    prev_position /= prev_position.w;
#else
    position = vec4(vs_in_position, 1.0);
    vertex_normal = vs_in_normal;
    vertex_tangent = vs_in_tangent;
    prev_position = position;
#endif

    vertex_normal = normalize(vertex_normal);
    vertex_tangent = normalize(vertex_tangent);

    mat4 local_matrix = is_instancing ? model * vs_in_isntance_matrix : model;

    vs_output.world_position = (local_matrix * position).xyz;
    vs_output.vertex_normal = vertex_normal;
    vs_output.vertex_color = vs_in_color;
    vs_output.tex_coord = vs_in_tex_coord * uv_tiling;

    vec3 bitangent = cross(vertex_tangent, vertex_normal);

    // Note : Normalization is very important because tangent_to_world may have been scaled..
    vs_output.tangent_to_world = local_matrix *
        mat4(vec4(vertex_tangent, 0.0), vec4(vertex_normal, 0.0), vec4(bitangent, 0.0), vec4(0.0, 0.0, 0.0, 1.0));

    position = VIEW_PROJECTION * local_matrix * position;
    prev_position = PREV_VIEW_PROJECTION * local_matrix * prev_position;

    vs_output.projection_pos = position;
    vs_output.prev_projection_pos = prev_position;

    gl_Position = position;
}
#endif