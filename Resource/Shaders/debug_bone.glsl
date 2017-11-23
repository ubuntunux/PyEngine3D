#version 430 core

#define SKELETAL 0

//----------- UNIFORM_BLOCK ---------------//

#include "scene_constants.glsl"

uniform mat4 mat1;
uniform mat4 mat2;


//----------- INPUT and OUTPUT ---------------//

struct VERTEX_INPUT
{
    vec3 position;
    vec4 color;
    vec3 normal;
    vec3 tangent;
    vec2 tex_coord;
#if SKELETAL
    vec4 bone_indicies;
    vec4 bone_weights;
#endif
};

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
layout (location = 0) in VERTEX_INPUT vs_input;
layout (location = 0) out VERTEX_OUTPUT vs_output;

void main() {
    vec3 local_pos = vs_input.position.xyz * vec3(0.1, 0.1, 0.1);
    if(vs_input.position.y > 0.0)
    {
        vs_output.world_position = (mat2 * vec4(local_pos, 1.0)).xyz;
    }
    else
    {
        vs_output.world_position = (mat1 * vec4(local_pos, 1.0)).xyz;
    }

#if SKELETAL
    vs_output.bone_indicies = vs_input.bone_indicies;
    vs_output.bone_weights = vs_input.bone_weights;
#endif

    gl_Position = PERSPECTIVE * VIEW * vec4(vs_output.world_position, 1.0);
}
#endif



#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    fs_output = vec4(1.0, 1.0, 1.0, 1.0);
}
#endif