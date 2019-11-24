#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "default_vs.glsl"


#ifdef FRAGMENT_SHADER
uniform uint object_id;

layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out float fs_ouptut;

void main()
{
    fs_ouptut = float(object_id);
}
#endif