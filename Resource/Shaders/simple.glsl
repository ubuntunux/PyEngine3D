#include "scene_constants.glsl"

uniform mat4 model;
uniform mat4 view_projection;
uniform vec4 diffuse_color;

//----------- VERTEX_SHADER ---------------//

#ifdef VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;

void main() {
    gl_Position = PROJECTION * VIEW * model * vec4(vs_in_position, 1.0);
}
#endif

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
layout (location = 0) out vec4 fs_output;

void main() {
    fs_output = vec4(1.0, 1.0, 0.0, 1.0);
}
#endif