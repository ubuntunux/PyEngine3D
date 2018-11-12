#include "utility.glsl"

vec4 SampleDepthtexture2D(sampler2D texDepth, vec4 SampleUV0, vec4 SampleUV1, float level)
{  
    vec4 SampleDepth;
    SampleDepth.x = texture2DLod(texDepth, SampleUV0.xy, level).x;
    SampleDepth.y = texture2DLod(texDepth, SampleUV0.zw, level).x;
    SampleDepth.z = texture2DLod(texDepth, SampleUV1.xy, level).x;
    SampleDepth.w = texture2DLod(texDepth, SampleUV1.zw, level).x;
    return SampleDepth;
}
 
vec4 RayCast(
    sampler2D texLinearDepth,
    mat4 matViewOrigin,
    mat4 matProjection,
    vec3 RayOriginTranslatedWorld,
    vec3 RayDirection,
    float Roughness,
    float ConeAngleWorld,
    float LinearDepth,
    int NumSteps,
    float StepOffset
)
{
    // avoid bugs with early returns inside of loops on certain platform compilers.
    vec4 Result = vec4(0, 0, 0, 1);
 
    vec4 RayStartV = matViewOrigin * vec4(RayOriginTranslatedWorld, 1);
    vec4 RayDirV = matViewOrigin * vec4(RayDirection * LinearDepth, 0);
    vec4 RayEndV = RayStartV + RayDirV;

    vec4 RayStartClip = matProjection * RayStartV;
    vec4 RayEndClip = matProjection * RayEndV;
 
    vec3 RayStartScreen = RayStartClip.xyz / RayStartClip.w;
    RayStartScreen.z = RayStartScreen.z * 0.5 + 0.5;

    vec3 RayEndScreen = RayEndClip.xyz / RayEndClip.w;
    RayEndScreen.z = RayEndScreen.z * 0.5 + 0.5;
 
    vec4 RayDepthClip = RayStartClip + matProjection * vec4(0, 0, LinearDepth, 0);
    vec3 RayDepthScreen = RayDepthClip.xyz / RayDepthClip.w;
    RayDepthScreen.z = RayDepthScreen.z * 0.5 + 0.5;
 
    vec3 RayStepScreen = RayEndScreen - RayStartScreen;
 
    {
        // Computes the scale down factor for RayStepScreen required to fit on the X and Y axis in order to clip it in the viewport
        float RayStepScreenInvFactor = 0.5 * length(RayStepScreen.xy);
        vec2 AbsRayStepScreen = abs(RayStepScreen.xy);
        vec2 S = (AbsRayStepScreen - max(abs(RayStepScreen.xy + RayStartScreen.xy * RayStepScreenInvFactor) - RayStepScreenInvFactor, 0.0f)) / AbsRayStepScreen;
 
        // Rescales RayStepScreen accordingly
        float RayStepFactor = min(S.x, S.y) / RayStepScreenInvFactor;
 
        RayStepScreen *= RayStepFactor;
    }
 
    vec3 RayStartUVz = vec3(RayStartScreen.xy * 0.5 + 0.5, RayStartScreen.z);
    vec3 RayStepUVz = vec3(RayStepScreen.xy * 0.5, RayStepScreen.z);
 
    float Step = 1.0 / NumSteps;
    float CompareTolerance = max(abs(RayStepUVz.z), abs(RayStartScreen.z - RayDepthScreen.z) * 4.0) * Step;
 
    float LastDiff = 0;
 
    RayStepUVz *= Step;
    vec3 RayUVz = RayStartUVz + RayStepUVz * StepOffset;
    float lod_level = 0.0;

    for (int i = 0; i < NumSteps; i += 4)
    {
        // Vectorized to group fetches
        vec4 SampleUV0 = RayUVz.xyxy + RayStepUVz.xyxy * vec4(1, 1, 2, 2);
        vec4 SampleUV1 = RayUVz.xyxy + RayStepUVz.xyxy * vec4(3, 3, 4, 4);
        vec4 SampleZ = RayUVz.zzzz + RayStepUVz.zzzz * vec4(1, 2, 3, 4);
 
        // Use lower res for farther samples
        vec4 SampleDepth = SampleDepthtexture2D(texLinearDepth, SampleUV0, SampleUV1, lod_level);
        SampleDepth = linear_depth_to_depth(SampleDepth);

        vec4 DepthDiff = SampleZ - SampleDepth;
 
        bvec4 Hit = bvec4(
            abs(DepthDiff[0] - CompareTolerance) < CompareTolerance,
            abs(DepthDiff[1] - CompareTolerance) < CompareTolerance,
            abs(DepthDiff[2] - CompareTolerance) < CompareTolerance,
            abs(DepthDiff[3] - CompareTolerance) < CompareTolerance
        );
 
        //if (any(Hit) && (SampleDepth.x < 1.0 && SampleDepth.y < 1.0 && SampleDepth.z < 1.0 && SampleDepth.w < 1.0))
        if (any(Hit))
        {
            float DepthDiff0 = DepthDiff[2];
            float DepthDiff1 = DepthDiff[3];
            float MinTime = 3;
 
            if (Hit[2])
            {
                DepthDiff0 = DepthDiff[1];
                DepthDiff1 = DepthDiff[2];
                MinTime = 2;
            }

            if (Hit[1])
            {
                DepthDiff0 = DepthDiff[0];
                DepthDiff1 = DepthDiff[1];
                MinTime = 1;
            }

            if (Hit[0])
            {
                DepthDiff0 = LastDiff;
                DepthDiff1 = DepthDiff[0];
                MinTime = 0;
            }
 
            // Find more accurate hit using line segment intersection
            float TimeLerp = clamp(DepthDiff0 / (DepthDiff0 - DepthDiff1), 0.0, 1.0);
            float IntersectTime = MinTime + TimeLerp;
            vec3 HitUVz = RayUVz + RayStepUVz * IntersectTime;
 
            Result = vec4(HitUVz, 0.5);
            break;
        }
 
        LastDiff = DepthDiff.w;
        RayUVz += 4 * RayStepUVz;
        lod_level += 4.0 / NumSteps;
    }

    return Result;
}