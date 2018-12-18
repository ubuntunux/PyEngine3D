#include "scene_constants.glsl"
#include "effect/common.glsl"

uniform sampler2D texture_diffuse;


struct VERTEX_OUTPUT
{
    vec3 world_position;
    vec3 vertex_normal;
    vec4 vertex_color;
    vec4 projection_pos;
    vec2 uv;
    vec2 next_uv;
    float sequence_ratio;
    float opacity;
};

#define INSTANCE_ID_LOCATION 12


#ifdef VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
layout (location = 5) in mat4 in_world_matrix;
layout (location = 9) in vec4 uvs;
layout (location = 10) in vec4 sequence_opacity;

layout (location = 0) out VERTEX_OUTPUT vs_output;
layout (location = INSTANCE_ID_LOCATION) flat out uint instanceID;


void main() {
    instanceID = gl_InstanceID.x;

    vec3 vertex_normal = normalize(vs_in_normal);
    vec3 vertex_tangent = normalize(vs_in_tangent);
    vec4 vertex_position = vec4(vs_in_position, 1.0);

    vec3 world_position = (in_world_matrix * vertex_position).xyz;

    vs_output.world_position = world_position.xyz;
    vs_output.vertex_normal = vertex_normal;
    vs_output.vertex_color = vs_in_color;

    vec3 bitangent = cross(vertex_tangent, vertex_normal);

    vs_output.projection_pos = VIEW_PROJECTION * vec4(world_position, 1.0);
    vec2 uv_size = vs_in_tex_coord.xy / vec2(PARTICLE_CELL_COUNT);
    vs_output.uv = uvs.xy + uv_size;
    vs_output.next_uv = uvs.zw + uv_size;
    vs_output.sequence_ratio = sequence_opacity.x;
    vs_output.opacity = sequence_opacity.y;

    gl_Position = vs_output.projection_pos;
}
#endif