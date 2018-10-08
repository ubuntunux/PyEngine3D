

#include "utility.glsl"
#include "scene_constants.glsl"
#include "default_vs.glsl"

//-------------- MATERIAL_COMPONENTS ---------------//

#include "default_material.glsl"

//----------- FRAGMENT_SHADER ---------------//


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec4 base_color = get_base_color(vs_output.tex_coord.xy);

    if(base_color.a < 0.333f)
    {
        discard;
    }

    fs_output = vec4(vec3(gl_FragCoord.z, 0.0, 0.0), 1.0);
}
#endif