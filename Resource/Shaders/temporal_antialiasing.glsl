//=================================================================================================
//
//  MSAA Filtering 2.0 Sample
//  by MJP
//  http://mynameismjp.wordpress.com/
//
//  All code licensed under the MIT license
//
//=================================================================================================

#include "scene_constants.glsl"
#include "utility.glsl"
#include "quad.glsl"


const float Pi = 3.141592f;

const int ClampModes_Disabled = 0;
const int ClampModes_RGB_Clamp = 1;
const int ClampModes_RGB_Clip = 2;
const int ClampModes_Variance_Clip = 3;

const int DilationModes_CenterAverage = 0;
const int DilationModes_DilateNearestDepth = 1;
const int DilationModes_DilateGreatestVelocity = 2;


const int ResolveFilterType = FilterTypes_BSpline;
const float ResolveFilterDiameter = 2.0;  // 0.0 ~ 6.0
const float ExposureFilterOffset = 2.0;     // -16.0 ~ 16.0
const float TemporalAABlendFactor = 0.9;    // 0.0 ~ 1.0
const int NeighborhoodClampMode = ClampModes_Variance_Clip;
const float VarianceClipGamma = 1.5;    // 0.0 ~ 2.0
const float LowFreqWeight = 0.25;   // 0.0 ~ 100.0
const float HiFreqWeight = 0.85;    // 0.0 ~ 100.0
const int DilationMode = DilationModes_DilateGreatestVelocity;
const int ReprojectionFilter = FilterTypes_CatmullRom;
const float ExposureScale = 0.0;    // -16.0 ~ 16.0
const float ManualExposure = -2.5;  // -10.0 ~ 10.0

const bool UseStandardReprojection = false;
const bool UseTemporalColorWeighting = false;
const bool InverseLuminanceFiltering = true;
const bool UseExposureFiltering = false;

uniform sampler2D texture_prev;
uniform sampler2D texture_input;
uniform sampler2D texture_velocity;
uniform sampler2D texture_linear_depth;


// From "Temporal Reprojection Anti-Aliasing"
// https://github.com/playdeadgames/temporal
vec3 ClipAABB(vec3 aabbMin, vec3 aabbMax, vec3 prevSample, vec3 avg)
{
    #if 1
        // note: only clips towards aabb center (but fast!)
        vec3 p_clip = 0.5 * (aabbMax + aabbMin);
        vec3 e_clip = 0.5 * (aabbMax - aabbMin);

        vec3 v_clip = prevSample - p_clip;
        vec3 v_unit = v_clip.xyz / e_clip;
        vec3 a_unit = abs(v_unit);
        float ma_unit = max(a_unit.x, max(a_unit.y, a_unit.z));

        if (ma_unit > 1.0)
        {
            return p_clip + v_clip / ma_unit;
        }
        else
        {
            return prevSample;// point inside aabb
        }
    #else
        vec3 r = prevSample - avg;
        vec3 rmax = aabbMax - avg.xyz;
        vec3 rmin = aabbMin - avg.xyz;

        const float eps = 0.000001f;

        if (r.x > rmax.x + eps)
            r *= (rmax.x / r.x);
        if (r.y > rmax.y + eps)
            r *= (rmax.y / r.y);
        if (r.z > rmax.z + eps)
            r *= (rmax.z / r.z);

        if (r.x < rmin.x - eps)
            r *= (rmin.x / r.x);
        if (r.y < rmin.y - eps)
            r *= (rmin.y / r.y);
        if (r.z < rmin.z - eps)
            r *= (rmin.z / r.z);

        return avg + r;
    #endif
}

vec3 Reproject(vec2 texCoord)
{
    vec2 inv_velocity_tex_size = 1.0 / textureSize(texture_velocity, 0).xy;
    vec2 velocity = vec2(0.0, 0.0);

    if(DilationMode == DilationModes_CenterAverage)
    {
        velocity += texture2D(texture_velocity, texCoord).xy;
    }
    else if(DilationMode == DilationModes_DilateNearestDepth)
    {
        vec2 inv_depth_tex_size = 1.0 / textureSize(texture_linear_depth, 0).xy;
        float closestDepth = 10.0f;
        for(int vy = -1; vy <= 1; ++vy)
        {
            for(int vx = -1; vx <= 1; ++vx)
            {
                vec2 neighborVelocity = texture2D(texture_velocity, texCoord + vec2(vx, vy) * inv_velocity_tex_size).xy;
                float neighborDepth = texture2DLod(texture_linear_depth, texCoord + vec2(vx, vy) * inv_depth_tex_size, 0.0).x;
                if(neighborDepth < closestDepth)
                {
                    velocity = neighborVelocity;
                    closestDepth = neighborDepth;
                }
            }
        }
    }
    else if(DilationMode == DilationModes_DilateGreatestVelocity)
    {
        float greatestVelocity = -1.0f;
        for(int vy = -1; vy <= 1; ++vy)
        {
            for(int vx = -1; vx <= 1; ++vx)
            {
                vec2 neighborVelocity = texture2D(texture_velocity, texCoord + vec2(vx, vy) * inv_velocity_tex_size).xy;
                float neighborVelocityMag = dot(neighborVelocity, neighborVelocity).x;
                if(dot(neighborVelocity, neighborVelocity) > greatestVelocity)
                {
                    velocity = neighborVelocity;
                    greatestVelocity = neighborVelocityMag;
                }
            }
        }
    }

    vec2 texture_prev_size = textureSize(texture_prev, 0).xy;
    vec2 reprojectedUV = texCoord - velocity;
    vec2 reprojectedPos = reprojectedUV * texture_prev_size;

    if(UseStandardReprojection)
    {
        return texture2D(texture_prev, reprojectedUV).xyz;
    }

    vec3 sum = vec3(0.0f);
    float totalWeight = 0.0f;

    for(int ty = -1; ty <= 2; ++ty)
    {
        for(int tx = -1; tx <= 2; ++tx)
        {
            vec2 samplePos = floor(reprojectedPos + vec2(tx, ty)) + 0.5f;
            vec3 reprojectedSample = texture2D(texture_prev, samplePos / texture_prev_size).xyz;

            vec2 sampleDist = abs(samplePos - reprojectedPos);
            float filterWeight = Filter(sampleDist.x, ReprojectionFilter, 1.0f, false) *
                                 Filter(sampleDist.y, ReprojectionFilter, 1.0f, false);

            if(InverseLuminanceFiltering)
            {
                float sampleLum = get_luminance(reprojectedSample);
                if(UseExposureFiltering)
                {
                    sampleLum *= exp2(ManualExposure - ExposureScale + ExposureFilterOffset);
                }
                filterWeight /= (1.0f + sampleLum);
            }

            sum += reprojectedSample * filterWeight;
            totalWeight += filterWeight;
        }
    }
    return max(sum / totalWeight, 0.0f);
}

vec4 ResolvePS(vec2 texCoord, vec2 pixelPos)
{
    vec3 sum = vec3(0.0f);
    float totalWeight = 0.0f;

    vec3 clrMin = vec3(99999999.0f);
    vec3 clrMax = vec3(-99999999.0f);

    vec3 m1 = vec3(0.0f);
    vec3 m2 = vec3(0.0f);
    float mWeight = 0.0f;

    vec2 texture_input_size = textureSize(texture_input, 0).xy;

    const float filterRadius = ResolveFilterDiameter / 2.0f;

    for(int y = -1; y <= 1; ++y)
    {
        for(int x = -1; x <= 1; ++x)
        {
            vec2 sampleOffset = vec2(x, y);
            vec2 sampleUV = texCoord + sampleOffset / texture_input_size;
            sampleUV = clamp(sampleUV, 0.0, 1.0);

            vec3 sample_color = texture2D(texture_input, sampleUV).xyz;

            vec2 sampleDist = abs(sampleOffset) / (ResolveFilterDiameter / 2.0f);

            float weight = Filter(sampleDist.x, ResolveFilterType, filterRadius, true) *
                           Filter(sampleDist.y, ResolveFilterType, filterRadius, true);
            clrMin = min(clrMin, sample_color);
            clrMax = max(clrMax, sample_color);

            if(InverseLuminanceFiltering)
            {
                float sampleLum = get_luminance(sample_color);
                if(UseExposureFiltering)
                {
                    sampleLum *= exp2(ManualExposure - ExposureScale + ExposureFilterOffset);
                }
                weight /= (1.0f + sampleLum);
            }

            sum += sample_color * weight;
            totalWeight += weight;

            m1 += sample_color;
            m2 += sample_color * sample_color;
            mWeight += 1.0f;
        }
    }

    vec4 result = texture2D(texture_input, texCoord);

    vec3 currColor = result.xyz;
    vec3 prevColor = Reproject(texCoord);

    if(NeighborhoodClampMode == ClampModes_RGB_Clamp)
    {
        prevColor = clamp(prevColor, clrMin, clrMax);
    }
    else if(NeighborhoodClampMode == ClampModes_RGB_Clip)
    {
        prevColor = ClipAABB(clrMin, clrMax, prevColor, m1 / mWeight);
    }
    else if(NeighborhoodClampMode == ClampModes_Variance_Clip)
    {
        vec3 mu = m1 / mWeight;
        vec3 sigma = sqrt(abs(m2 / mWeight - mu * mu));
        vec3 minc = mu - VarianceClipGamma * sigma;
        vec3 maxc = mu + VarianceClipGamma * sigma;
        prevColor = ClipAABB(minc, maxc, prevColor, mu);
    }

    vec3 weightA = vec3(clamp(1.0f - TemporalAABlendFactor, 0.0, 1.0));
    vec3 weightB = vec3(clamp(TemporalAABlendFactor, 0.0, 1.0));

    if(UseTemporalColorWeighting)
    {
        vec3 temporalWeight = clamp(abs(clrMax - clrMin) / currColor, 0.0, 1.0);
        weightB = clamp(mix(vec3(LowFreqWeight), vec3(HiFreqWeight), temporalWeight), 0.0, 1.0);
        weightA = 1.0f - weightB;
    }

    if(InverseLuminanceFiltering)
    {
        weightA /= (1.0f + get_luminance(currColor));
        weightB /= (1.0f + get_luminance(prevColor));
    }

    result.xyz = (currColor * weightA + prevColor * weightB) / (weightA + weightB);

    return result;
}


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    fs_output = ResolvePS(vs_output.tex_coord.xy, gl_FragCoord.xy);
}
#endif // FRAGMENT_SHADER