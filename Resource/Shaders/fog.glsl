

#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_linear_depth;

#ifdef MATERIAL_COMPONENTS
    uniform vec3 fog_color;
#endif


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;

    float linear_depth = texture(texture_linear_depth, tex_coord).x;
    fs_output.xyz = fog_color;
    fs_output.a = linear_depth < NEAR_FAR.y ? pow(clamp(linear_depth * 0.01, 0.0, 1.0), 2.0) : 0.0;
}
#endif // FRAGMENT_SHADER