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
    vec2 texcoord = vs_output.texcoord.xy;
    vec4 color = texture(texture_diffuse, vs_output.texcoord.xy);
    fs_output.xyz = pow(color.xyz, vec3(1.0 / 2.2));
    fs_output.a = 1.0;
}
#endif // FRAGMENT_SHADER