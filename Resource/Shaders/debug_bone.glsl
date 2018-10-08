#define SKELETAL 0

#include "scene_constants.glsl"

uniform mat4 matrix1;
uniform mat4 matrix2;

struct VERTEX_OUTPUT
{
    vec3 world_position;
#if SKELETAL
    vec4 bone_indicies;
    vec4 bone_weights;
#endif
};

//----------- VERTEX_SHADER ---------------//

#ifdef VERTEX_SHADER
    layout (location = 0) in vec3 vs_in_position;
    layout (location = 1) in vec4 vs_in_color;
    layout (location = 2) in vec3 vs_in_normal;
    layout (location = 3) in vec3 vs_in_tangent;
    layout (location = 4) in vec2 vs_in_tex_coord;
#if SKELETAL
    layout (location = 5) in vec4 vs_in_bone_indicies;
    layout (location = 6) in vec4 vs_in_bone_weights;
#endif

layout (location = 0) out VERTEX_OUTPUT vs_output;

void main() {
    vec3 local_pos = vs_in_position.xyz * vec3(0.1, 0.1, 0.1);
    if(vs_in_position.y > 0.0)
    {
        vs_output.world_position = (matrix2 * vec4(local_pos, 1.0)).xyz;
    }
    else
    {
        vs_output.world_position = (matrix1 * vec4(local_pos, 1.0)).xyz;
    }

#if SKELETAL
    vs_output.bone_indicies = vs_in_bone_indicies;
    vs_output.bone_weights = vs_in_bone_weights;
#endif

    gl_Position = PROJECTION * VIEW * vec4(vs_output.world_position, 1.0);
}
#endif


// FRAGMENT SHADER

#ifdef FRAGMENT_SHADER
    layout (location = 0) in vec3 vs_out_world_position;
#if SKELETAL
    layout (location = 1) in vec4 vs_out_bone_indicies;
    layout (location = 2) in vec4 vs_out_bone_weights;
#endif
layout (location = 0) out vec4 fs_output;

void main() {
    fs_output = vec4(1.0, 1.0, 1.0, 1.0);
}
#endif