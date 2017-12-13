#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform bool copy_alpha;
uniform bool mirror_x;
uniform sampler2D texture_source;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 texcoord = vs_output.tex_coord.xy;

    if(mirror_x)
    {
        texcoord.x = 1.0f - texcoord.x;
    }

    fs_output = texture(texture_source, texcoord);

    if(!copy_alpha)
    {
        fs_output.w = 1.0f;
    }
}
#endif // FRAGMENT_SHADER