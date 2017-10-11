#version 430 core

#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_ssao;
uniform float exposure = 1.0;
uniform bool is_render_ssao;

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

const float A = 0.15;
const float B = 0.50;
const float C = 0.10;
const float D = 0.20;
const float E = 0.02;
const float F = 0.30;
const float W = 11.2;
const float ExposureBias = 2.0f;

vec3 Uncharted2Tonemap(vec3 x)
{
     return ((x*(A*x+C*B)+D*E)/(x*(A*x+B)+D*F))-E/F;
}

void main() {
    vec3 texColor = texture(texture_diffuse, vs_output.texcoord.xy).xyz;
    if(is_render_ssao)
    {
        texColor *= texture(texture_ssao, vs_output.texcoord.xy).xxx;
    }

    texColor *= exposure;  // Hardcoded Exposure Adjustment
    texColor = Uncharted2Tonemap(texColor * ExposureBias);
    vec3 whiteScale = 1.0f / Uncharted2Tonemap(vec3(W));
    fs_output.xyz = pow(texColor * whiteScale, vec3(1.0 / 2.2));
    fs_output.a = 1.0;
}
#endif // FRAGMENT_SHADER