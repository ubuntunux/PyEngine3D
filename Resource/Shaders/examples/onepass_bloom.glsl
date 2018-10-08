#include "utility.glsl"
#include "quad.glsl"

uniform float bloom_threshold_min;
uniform float bloom_threshold_max;

uniform sampler2D texture_diffuse;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

vec3 makeBloom(float lod, vec2 offset, vec2 bCoord, vec2 pixelSize){
    offset += pixelSize;

    float lodFactor = exp2(lod);

    vec3 bloom = vec3(0.0);
    vec2 scale = lodFactor * pixelSize;

    vec2 coord = (bCoord.xy-offset)*lodFactor;
    float totalWeight = 0.0;

    if (any(greaterThanEqual(abs(coord - 0.5), scale + 0.5)))
        return vec3(0.0);

    for (int i = -5; i < 5; i++)
    {
        for (int j = -5; j < 5; j++)
        {
            float wg = pow(1.0 - length(vec2(i,j)) * 0.125, 6.0);
            vec3 color = texture2D(texture_diffuse,coord + vec2(i,j) * scale + lodFactor * pixelSize, lod).rgb;

            float luminance = max(0.01, get_luminance(color));
            color = color * min(bloom_threshold_max, max(0.0, luminance - bloom_threshold_min)) / luminance;

            bloom += color * wg;
            totalWeight += wg;
        }
    }

    bloom /= totalWeight;

    return bloom;
}

void main() {
    vec2 uv = vs_output.tex_coord.xy;
    vec2 pixelSize = 1.0 / textureSize(texture_diffuse, 0);
	vec3 blur = makeBloom(2.0, vec2(0.0,0.0), uv, pixelSize);
		blur += makeBloom(3.0, vec2(0.3,0.0), uv, pixelSize);
		blur += makeBloom(4.0, vec2(0.0,0.3), uv, pixelSize);
		blur += makeBloom(5.0, vec2(0.1,0.3), uv, pixelSize);
		blur += makeBloom(6.0, vec2(0.2,0.3), uv, pixelSize);

    fs_output = vec4(blur, 1.0);
}
#endif // FRAGMENT_SHADER