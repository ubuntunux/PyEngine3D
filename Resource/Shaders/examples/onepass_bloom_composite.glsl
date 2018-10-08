#include "quad.glsl"

uniform float bloom_intensity;

uniform sampler2D texture_bloom;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

vec3 bloomTile(float lod, vec2 offset, vec2 uv)
{
    return texture2D(texture_bloom, uv / exp2(lod) + offset).rgb;
}

vec3 getBloom(vec2 uv)
{
    vec3 blur = vec3(0.0);
    blur += bloomTile(2.0, vec2(0.0,0.0), uv);
    blur += bloomTile(3.0, vec2(0.3,0.0), uv) * 1.3;
    blur += bloomTile(4.0, vec2(0.0,0.3), uv) * 1.6;
    blur += bloomTile(5.0, vec2(0.1,0.3), uv) * 1.9;
    blur += bloomTile(6.0, vec2(0.2,0.3), uv) * 2.2;
    return blur;
}

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;
    fs_output.xyz = getBloom(tex_coord) * bloom_intensity;
    fs_output.w = 1.0;
}
#endif // FRAGMENT_SHADER