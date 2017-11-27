

//----------- UNIFORM_BLOCK ---------------//

#include "scene_constants.glsl"

uniform mat4 model;
uniform mat4 view_projection;
uniform vec4 diffuse_color;

//----------- INPUT and OUTPUT ---------------//

struct VERTEX_INPUT
{
    vec3 position;
    vec4 color;
    vec3 normal;
    vec3 tangent;
    vec2 tex_coord;
};

//----------- VERTEX_SHADER ---------------//

#ifdef VERTEX_SHADER
layout (location = 0) in VERTEX_INPUT vs_input;

void main() {
    gl_Position = PERSPECTIVE * VIEW * model * vec4(vs_input.position, 1.0);
}
#endif // VERTEX_SHADER

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
layout (location = 0) out vec4 fs_output;

void main() {
    fs_output = vec4(1.0, 1.0, 0.0, 1.0);
}
#endif // FRAGMENT_SHADER