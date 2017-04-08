#version 430 core

#include "quad.glsl"

//-------------- MATERIAL_COMPONENTS ---------------//

#ifdef MATERIAL_COMPONENTS
    uniform sampler2D texture_diffuse;
#endif

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    vec4 color = texture(texture_diffuse, vs_output.texcoord.xy);
    fs_output = color;
}
#endif // FRAGMENT_SHADER