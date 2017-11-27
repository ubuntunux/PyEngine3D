#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "default_material.glsl"
#include "default_vs.glsl"


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;

layout (location = 0) out vec4 fs_normal;
layout (location = 1) out vec2 fs_velocity;

void main() {
    vec4 base_color = get_base_color(vs_output.tex_coord.xy);

#if TRANSPARENT_MATERIAL == 1
    base_color.a *= opacity;
#endif

#if TRANSPARENT_MATERIAL != 1
    if(base_color.a < 0.333f)
    {
        discard;
    }
#endif

    vec3 N = get_normal(vs_output.tex_coord.xy);

    // Note : Normalization is very important because tangent_to_world may have been scaled..
    N = normalize((vs_output.tangent_to_world * vec4(N, 0.0)).xyz) * 0.5 + 0.5;
    fs_normal = vec4(N, 1.0);

    fs_velocity = (vs_output.projection_pos.xy / vs_output.projection_pos.w) -
        (vs_output.prev_projection_pos.xy / vs_output.prev_projection_pos.w);
    // NDC coord -> Screen Coord
    fs_velocity *= 0.5;
}
#endif