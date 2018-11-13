#include "utility.glsl"
#include "PCFKernels.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_input;
uniform sampler2D texture_resolve_prev;
uniform sampler2D texture_velocity;

const float VarianceClipGamma = 1.5;

vec4 ClipAABB(vec4 aabbMin, vec4 aabbMax, vec4 prevSample, vec4 avg)
{
    vec4 p_clip = 0.5 * (aabbMax + aabbMin);
    vec4 e_clip = 0.5 * (aabbMax - aabbMin);

    vec4 v_clip = prevSample - p_clip;
    vec4 v_unit = v_clip / e_clip;
    vec4 a_unit = abs(v_unit);

    float ma_unit = max(a_unit.x, max(a_unit.y, max(a_unit.z, a_unit.w)));

    if (ma_unit > 1.0)
    {
        return p_clip + v_clip / ma_unit;
    }
    else
    {
        return prevSample;
    }
}

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;


void main()
{
    vec2 uv = vs_output.tex_coord;
    vec4 sum = vec4(0.0);
    float totalWeight = 0.0;
    vec4 clrMin = vec4(99999999.0);
    vec4 clrMax = vec4(-99999999.0);
    vec4 m1 = vec4(0.0);
    vec4 m2 = vec4(0.0);
    float mWeight = 0.0;

    vec2 texture_input_size = textureSize(texture_input, 0).xy;
    vec4 currColor = vec4(0.0);

    for (int y = -1; y <= 1; ++y)
    {
        for (int x = -1; x <= 1; ++x)
        {
            vec2 sampleOffset = vec2(x, y);
            vec2 sampleUV = saturate(uv + sampleOffset / texture_input_size);
            vec4 sampleColor = texture2DLod(texture_input, sampleUV, 0.0);

            if(0 == x && 0 == y)
            {
                currColor = sampleColor;
                currColor.w = saturate(currColor.w);
            }

            vec2 sampleDist = abs(sampleOffset);
            float weight = Filter(sampleDist.x, FilterTypes_BSpline, 1.0, true) * Filter(sampleDist.y, FilterTypes_BSpline, 1.0, true);
            clrMin = min(clrMin, sampleColor);
            clrMax = max(clrMax, sampleColor);

            // inverse luminance filtering
            weight *= 1.0f / (1.0f + get_luminance(sampleColor.xyz));
            sum += sampleColor * weight;
            totalWeight += weight;

            m1 += sampleColor;
            m2 += sampleColor * sampleColor;
            mWeight += 1.0;
        }
    }

    // Anti Aliasing
    vec2 velocity = texture2DLod(texture_velocity, uv, 0.0).xy;
    vec4 prevColor = texture2DLod(texture_resolve_prev, uv - velocity, 0.0);
    prevColor.w = saturate(prevColor.w);

    // NeighborhoodClampMode
    vec4 mu = currColor; // important, use currColor instead of (m1 / mWeight) beacause blurry result..
    vec4 sigma = sqrt(abs(m2 / mWeight - mu * mu));
    vec4 minc = mu - VarianceClipGamma * sigma;
    vec4 maxc = mu + VarianceClipGamma * sigma;
    prevColor = ClipAABB(minc, maxc, prevColor, m1 / mWeight);

    vec4 weightB = mix(vec4(0.9f), vec4(0.99f), saturate(abs(clrMax - clrMin) / currColor));
    vec4 weightA = 1.0f - weightB;

    // inverse luminance filtering
    weightA = weightA / (1.0f + get_luminance(currColor.xyz));
    weightB = weightB / (1.0f + get_luminance(prevColor.xyz));

    weightA = weightA * (1.0 + currColor.w * 10.0);
    weightB = weightB * (1.0 + prevColor.w * 10.0);

    fs_output = (currColor * weightA + prevColor * weightB) / (weightA + weightB);

    fs_output.xyz = max(vec3(0.0), fs_output.xyz);
    fs_output.w = saturate(fs_output.w);
}
#endif