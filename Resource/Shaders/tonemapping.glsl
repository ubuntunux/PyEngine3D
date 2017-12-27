

#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform float exposure;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

const float A = 0.15;
const float B = 0.50;
const float C = 0.10;
const float D = 0.20;
const float E = 0.02;
const float F = 0.30;
const float W = 11.2;
const float ExposureBias = 2.0f;


vec3 Uncharted2TonemapFunction(vec3 x)
{
     return ((x*(A*x+C*B)+D*E)/(x*(A*x+B)+D*F))-E/F;
}

vec3 Uncharted2Tonemap(vec3 hdrColor)
{
    hdrColor *= exposure;  // Hardcoded Exposure Adjustment
    hdrColor = Uncharted2TonemapFunction(hdrColor * ExposureBias);
    vec3 whiteScale = 1.0f / Uncharted2TonemapFunction(vec3(W));
    return pow(hdrColor * whiteScale, vec3(1.0 / 2.2));
}

vec3 ReinhardTonemap(vec3 hdrColor)
{
    vec3 mapped = hdrColor / (hdrColor + vec3(1.0));
    return pow(mapped, vec3(1.0 / 2.2));
}

vec3 SimpleTonemap(vec3 hdrColor)
{
    // Exposure tone mapping
    vec3 mapped = vec3(1.0) - exp(-hdrColor * exposure);
    return pow(mapped, vec3(1.0 / 2.2));
}

float vignetting(vec2 uv, float inner_value, float outter_value)
{
    float f = smoothstep(0.0, 1.0, length(uv - vec2(0.5)));
    return mix(inner_value, outter_value, f * f);
}

void main() {
    vec3 texColor = texture(texture_diffuse, vs_output.tex_coord.xy).xyz;
    fs_output.xyz = Uncharted2Tonemap(texColor);
    fs_output.xyz *= vignetting(vs_output.tex_coord.xy, 1.0, 0.0);
    fs_output.a = 1.0;
}
#endif // GL_FRAGMENT_SHADER
