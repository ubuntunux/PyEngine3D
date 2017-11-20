vec4 ScreenPositionScaleBias = vec4(0.5f, -0.5f, 0.5f, 0.5f);
 
// high frequency dither pattern appearing almost random without banding steps
//note: from "NEXT GENERATION POST PROCESSING IN CALL OF DUTY: ADVANCED WARFARE"
//      http://advances.realtimerendering.com/s2014/index.html
// Epic extended by FrameId
// ~7 ALU operations (2 frac, 3 mad, 2 *)
// @return 0..1
float InterleavedGradientNoise(vec2 uv, float FrameId)
{
    // magic values are found by experimentation
    uv += FrameId * (vec2(47, 17) * 0.695f);
 
    vec3 magic = vec3(0.06711056f, 0.00583715f, 52.9829189f);
    return fract(magic.z * fract(dot(uv, magic.xy)));
}
 
float ClampedPow(float X, float Y)
{
    return pow(max(abs(X), 0.000001f), Y);
}
 
uint MortonCode(uint x)
{
    x = (x ^ (x << 2)) & 0x33333333;
    x = (x ^ (x << 1)) & 0x55555555;
    return x;
}
 
uint ReverseBits32(uint bits)
{
    bits = (bits << 16) | (bits >> 16);
    bits = ((bits & 0x00ff00ff) << 8) | ((bits & 0xff00ff00) >> 8);
    bits = ((bits & 0x0f0f0f0f) << 4) | ((bits & 0xf0f0f0f0) >> 4);
    bits = ((bits & 0x33333333) << 2) | ((bits & 0xcccccccc) >> 2);
    bits = ((bits & 0x55555555) << 1) | ((bits & 0xaaaaaaaa) >> 1);
    return bits;
}
 
uint ReverseUIntBits(uint bits)
{
    //bits = ( bits << 16) | ( bits >> 16);
    //bits = ( (bits & 0x00ff00ff) << 8 ) | ( (bits & 0xff00ff00) >> 8 );
    //bits = ( (bits & 0x0f0f0f0f) << 4 ) | ( (bits & 0xf0f0f0f0) >> 4 );
    bits = ((bits & 0x33333333) << 2) | ((bits & 0xcccccccc) >> 2);
    bits = ((bits & 0x55555555) << 1) | ((bits & 0xaaaaaaaa) >> 1);
    return bits;
}
 
vec2 Hammersley(uint Index, uint NumSamples, uvec2 Random)
{
    float E1 = fract(float(Index) / NumSamples + float(Random.x & 0xffff) / (1 << 16));
    float E2 = float(ReverseBits32(Index) ^ Random.y) * 2.3283064365386963e-10;
    return vec2(E1, E2);
}
 
// @param xy should be a integer position (e.g. pixel position on the screen), repeats each 128x128 pixels
// similar to a texture lookup but is only ALU
// ~13 ALU operations (3 frac, 6 *, 4 mad)
float PseudoRandom(vec2 xy)
{
    vec2 pos = fract(xy / 128.0f) * 128.0f + vec2(-64.340622f, -72.465622f);
 
    // found by experimentation
    return fract(dot(pos.xyx * pos.xyy, vec3(20.390625f, 60.703125f, 2.4281209f)));
}

float Luminance(vec3 LinearColor)
{
    return dot(LinearColor, vec3(0.3, 0.59, 0.11));
}
 
vec4 ImportanceSampleBlinn(vec2 E, float Roughness)
{
    float PI = 3.14159265f;
    float m = Roughness * Roughness;
    float n = 2 / (m*m) - 2;
 
    float Phi = 2 * PI * E.x;
    float CosTheta = ClampedPow(E.y, 1 / (n + 1));
    float SinTheta = sqrt(1 - CosTheta * CosTheta);
 
    // TODO, TEST : swap y z
    vec3 H;
    H.x = SinTheta * cos(Phi);
    /*H.y = SinTheta * sin(Phi);
    H.z = CosTheta;*/
    H.y = CosTheta;
    H.z = SinTheta * sin(Phi);
 
    float D = (n + 2) / (2 * PI) * ClampedPow(CosTheta, n);
    float PDF = D * CosTheta;
 
    return vec4(H, PDF);
}
 
mat3 GetTangentBasis(vec3 TangentY)
{
    vec3 UpVector = abs(TangentY.z) < 0.999 ? vec3(0, 1, 0) : vec3(0, 0, 1);
    vec3 TangentX = normalize(cross(UpVector, TangentY));
    vec3 TangentZ = cross(TangentY, TangentX);
    return mat3(TangentX, TangentY, TangentZ);
}
 
vec3 TangentToWorld(vec3 vector, vec3 TangentY)
{
    return GetTangentBasis(TangentY) * vector;
}

vec2 ReprojectHit(mat4 matInvViewOriginProjection, mat4 matPrevViewOriginProjection, vec3 HitUVz)
{
    vec4 ThisClip = vec4(HitUVz.xy * 2.0 - 1.0, HitUVz.z, 1);
    vec4 PrevClip = matPrevViewOriginProjection * matInvViewOriginProjection * ThisClip;
    PrevClip.xyz /= PrevClip.w;
    return PrevClip.xy;
}
 
vec4 SampleScreenColor(sampler2D texPrevSceneColor, vec2 UV)
{
    vec4 OutColor;
    OutColor.xyz = textureLod(texPrevSceneColor, UV, 0.0).xyz;
    OutColor.w = 1;
 
    // Off screen masking
    vec2 ScreenPos = UV * 2.0 - 1.0;
 
    // ver1
    //vec2 Vignette = saturate(abs(ScreenPos) * 5.0 - 4.0);
    //OutColor.w *= saturate(1.0 - dot(Vignette, Vignette));
 
    // ver2
    float sharpen = 0.7f;
    vec2 Vignette = clamp((abs(ScreenPos) - sharpen) / (1.0 - sharpen), 0.0, 1.0);
    OutColor.w *= clamp(1.0 - length(Vignette), 0.0, 1.0);

    return OutColor;
}
 
vec4 SampleDepthTexture(sampler2D texDepth, vec4 SampleUV0, vec4 SampleUV1)
{  
    vec4 SampleDepth;
    SampleDepth.x = textureLod(texDepth, SampleUV0.xy, 0.0).x;
    SampleDepth.y = textureLod(texDepth, SampleUV0.zw, 0.0).x;
    SampleDepth.z = textureLod(texDepth, SampleUV1.xy, 0.0).x;
    SampleDepth.w = textureLod(texDepth, SampleUV1.zw, 0.0).x;
    return SampleDepth;
}

float ConvertToDeviceZ(mat4 matrix, float scene_depth)
{
    vec4 result = matrix * vec4(0.0, 0.0, scene_depth, 0.0);
    return (result.z / result.w) * 0.5 + 0.5;
}

float ConvertToDeviceZ(float m33, float m43, float scene_depth)
{
    return m33 + m43 / scene_depth;
}
 
vec4 RayCast(
    sampler2D texDepthRaw,
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
    float CompareTolerance = max(abs(RayStepUVz.z), (RayStartScreen.z - RayDepthScreen.z) * 4.0) * 0.1;
 
    float LastDiff = 0;
 
    RayStepUVz *= Step;
    vec3 RayUVz = RayStartUVz + RayStepUVz * StepOffset;

    for (int i = 0; i < NumSteps; i += 4)
    {
        // Vectorized to group fetches
        vec4 SampleUV0 = RayUVz.xyxy + RayStepUVz.xyxy * vec4(1, 1, 2, 2);
        vec4 SampleUV1 = RayUVz.xyxy + RayStepUVz.xyxy * vec4(3, 3, 4, 4);
        vec4 SampleZ = RayUVz.zzzz + RayStepUVz.zzzz * vec4(1, 2, 3, 4);
 
        // Use lower res for farther samples
        vec4 SampleDepth = SampleDepthTexture(texDepthRaw, SampleUV0, SampleUV1);

        vec4 DepthDiff = SampleZ - SampleDepth;
 
        bvec4 Hit = bvec4(
            abs(DepthDiff[0] - CompareTolerance) < CompareTolerance,
            abs(DepthDiff[1] - CompareTolerance) < CompareTolerance,
            abs(DepthDiff[2] - CompareTolerance) < CompareTolerance,
            abs(DepthDiff[3] - CompareTolerance) < CompareTolerance
        );
 
        // if (any(Hit) && all(SampleDepth < 1.0))  // Sky Clipping
        if (Hit[0] || Hit[1] || Hit[2] || Hit[3])
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
    }

    return Result;
}