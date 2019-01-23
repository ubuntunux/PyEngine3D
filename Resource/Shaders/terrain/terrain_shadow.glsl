#include "terrain/terrain_render_vs.glsl"

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;

layout (location = 0) out vec4 fs_output;

void main()
{
    fs_output = vec4(vec3(gl_FragCoord.z, 0.0, 0.0), 1.0);
}
#endif
