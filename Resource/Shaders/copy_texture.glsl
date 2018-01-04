#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform bool copy_alpha;
uniform sampler2D texture_source;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 texcoord = vs_output.tex_coord.xy;
    fs_output = texture(texture_source, texcoord);

}
#endif // GL_FRAGMENT_SHADER