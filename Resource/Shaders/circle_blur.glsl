#include "utility.glsl"
#include "quad.glsl"

uniform int loop_count;
uniform float radius;
uniform sampler2D texture_color;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;
    fs_output.xyz += texture2D(texture_color, tex_coord).xyz;

    float texel_radius = radius / length(textureSize(texture_color, 0));
    float rad_step = TWO_PI / float(loop_count);
    float rad = 0.0;
    for(int i=0; i<loop_count; ++i)
    {
        rad += rad_step;
        fs_output.xyz += texture2D(texture_color, tex_coord + vec2(sin(rad), cos(rad)) * texel_radius).xyz;
    }
    fs_output.xyz /= (loop_count + 1);
    fs_output.w = 1.0;
}
#endif // FRAGMENT_SHADER