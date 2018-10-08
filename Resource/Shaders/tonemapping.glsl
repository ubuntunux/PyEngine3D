#include "blending.glsl"
#include "quad.glsl"

uniform bool is_render_tonemapping;
uniform float exposure;
uniform float contrast;
uniform sampler2D texture_diffuse;

uniform bool is_render_bloom;
uniform float bloom_intensity;
uniform sampler2D texture_bloom0;
uniform sampler2D texture_bloom1;
uniform sampler2D texture_bloom2;
uniform sampler2D texture_bloom3;
uniform sampler2D texture_bloom4;

uniform bool is_render_light_shaft;
uniform sampler2D texture_light_shaft;

#ifdef FRAGMENT_SHADER
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
    hdrColor *= exposure;
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
    vec2 tex_coord = vs_output.tex_coord.xy;
    vec3 texColor = texture2D(texture_diffuse, tex_coord).xyz;

    vec3 bloom = vec3(0.0);
    if(is_render_bloom)
    {
        bloom += texture2D(texture_bloom0, tex_coord).xyz;
        bloom += texture2D(texture_bloom1, tex_coord).xyz;
        bloom += texture2D(texture_bloom2, tex_coord).xyz;
        bloom += texture2D(texture_bloom3, tex_coord).xyz;
        bloom += texture2D(texture_bloom4, tex_coord).xyz;
        bloom *= bloom_intensity;
    }
    texColor += bloom;

    vec3 light_shaft = vec3(0.0);
    if(is_render_light_shaft)
    {
        light_shaft = texture2D(texture_light_shaft, tex_coord).xyz;
    }
    texColor += light_shaft;

    if(is_render_tonemapping)
    {
        texColor = Uncharted2Tonemap(texColor);
        texColor *= vignetting(tex_coord, 1.0, 0.0);
    }
    else
    {
        texColor = pow(texColor, vec3(1.0 / 2.2));
    }

    fs_output.xyz = Contrast(texColor, contrast);
    fs_output.a = 1.0;
}
#endif // FRAGMENT_SHADER
