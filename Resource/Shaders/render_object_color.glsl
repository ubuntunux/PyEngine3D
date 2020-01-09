#include "utility.glsl"
#include "scene_constants.glsl"
#include "default_vs.glsl"

uniform vec4 color;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    fs_output = color;
}
#endif