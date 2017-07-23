#version 430 core

#define SKELETAL 0

//----------- UNIFORM_BLOCK ---------------//

#include "scene_constants.glsl"

uniform mat4 mat1;
uniform mat4 mat2;


//----------- INPUT and OUTPUT ---------------//

struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 texcoord;
#if SKELETAL
    layout(location=5) vec4 bone_indicies;
    layout(location=6) vec4 bone_weights;
#endif
};

struct VERTEX_OUTPUT
{
    vec3 worldPosition;
#if SKELETAL
    vec4 bone_indicies;
    vec4 bone_weights;
#endif
};

//----------- VERTEX_SHADER ---------------//

#ifdef VERTEX_SHADER
in VERTEX_INPUT vs_input;
out VERTEX_OUTPUT vs_output;

void main() {
    vec3 local_pos = vs_input.position.xyz * vec3(0.1, 0.1, 0.1);
    if(vs_input.position.y > 0.0)
    {
        vs_output.worldPosition = (mat2 * vec4(local_pos, 1.0)).xyz;
    }
    else
    {
        vs_output.worldPosition = (mat1 * vec4(local_pos, 1.0)).xyz;
    }

#if SKELETAL
    vs_output.bone_indicies = vs_input.bone_indicies;
    vs_output.bone_weights = vs_input.bone_weights;
#endif

    gl_Position = perspective * view * vec4(vs_output.worldPosition, 1.0);
}
#endif

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    fs_output = vec4(1.0, 1.0, 1.0, 1.0);
}
#endif