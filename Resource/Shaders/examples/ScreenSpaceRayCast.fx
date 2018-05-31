#include "D3DDefine.fx"
#include "Encode.fx"
#include "DepthRead.fxh"
#include "OutdoorScattering.fx"

#define USE_HZB 1

const float4 ScreenPositionScaleBias = float4(0.5f, -0.5f, 0.5f, 0.5f);

// high frequency dither pattern appearing almost random without banding steps
//note: from "NEXT GENERATION POST PROCESSING IN CALL OF DUTY: ADVANCED WARFARE"
// http://advances.realtimerendering.com/s2014/index.html
// Epic extended by FrameId
// ~7 ALU operations (2 frac, 3 mad, 2 *)
// @return 0..1
float InterleavedGradientNoise(float2 uv, float FrameId)
{
// magic values are found by experimentation
uv += FrameId * (float2(47, 17) * 0.695f);

const float3 magic = float3(0.06711056f, 0.00583715f, 52.9829189f);
return frac(magic.z * frac(dot(uv, magic.xy)));
}

float ClampedPow(float X, float Y)
{
return pow(max(abs(X), 0.000001f), Y);
}

uint MortonCode(uint x)
{
//x = (x ^ (x << 8)) & 0x00ff00ff;
//x = (x ^ (x << 4)) & 0x0f0f0f0f;
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

float2 Hammersley(uint Index, uint NumSamples, uint2 Random)
{
float E1 = frac((float)Index / NumSamples + float(Random.x & 0xffff) / (1 << 16));
float E2 = float(ReverseBits32(Index) ^ Random.y) * 2.3283064365386963e-10;
return float2(E1, E2);
}

// @param xy should be a integer position (e.g. pixel position on the screen), repeats each 128x128 pixels
// similar to a texture lookup but is only ALU
// ~13 ALU operations (3 frac, 6 *, 4 mad)
float PseudoRandom(float2 xy)
{
float2 pos = frac(xy / 128.0f) * 128.0f + float2(-64.340622f, -72.465622f);

// found by experimentation
return frac(dot(pos.xyx * pos.xyy, float3(20.390625f, 60.703125f, 2.4281209f)));
}

// 3D random number generator inspired by PCGs (permuted congruential generator)
// Using a **simple** Feistel cipher in place of the usual xor shift permutation step
// @param v = 3D integer coordinate
// @return three elements w/ 16 random bits each (0-0xffff).
// ~8 ALU operations for result.x (7 mad, 1 >>)
// ~10 ALU operations for result.xy (8 mad, 2 >>)
// ~12 ALU operations for result.xyz (9 mad, 3 >>)
uint3 Rand3DPCG16(int3 p)
{
// taking a signed int then reinterpreting as unsigned gives good behavior for negatives
uint3 v = uint3(p);

// Linear congruential step. These LCG constants are from Numerical Recipies
// For additional #'s, PCG would do multiple LCG steps and scramble each on output
// So v here is the RNG state
v = v * 1664525u + 1013904223u;

// PCG uses xorshift for the final shuffle, but it is expensive (and cheap
// versions of xorshift have visible artifacts). Instead, use simple MAD Feistel steps
//
// Feistel ciphers divide the state into separate parts (usually by bits)
// then apply a series of permutation steps one part at a time. The permutations
// use a reversible operation (usually ^) to part being updated with the result of
// a permutation function on the other parts and the key.
//
// In this case, I'm using v.x, v.y and v.z as the parts, using + instead of ^ for
// the combination function, and just multiplying the other two parts (no key) for 
// the permutation function.
//
// That gives a simple mad per round.
v.x += v.y*v.z;
v.y += v.z*v.x;
v.z += v.x*v.y;
v.x += v.y*v.z;
v.y += v.z*v.x;
v.z += v.x*v.y;

// only top 16 bits are well shuffled
return v >> 16u;
}

float GetRoughnessFade(in float Roughness)
{
// mask SSR to reduce noise and for better performance, roughness of 0 should have SSR, at MaxRoughness we fade to 0
const float RoughnessMask = -6.66666651f;
return min(Roughness * RoughnessMask + 2.0, 1.0);
}

float Luminance(float3 LinearColor)
{
return dot(LinearColor, float3(0.3, 0.59, 0.11));
}

float4 ImportanceSampleBlinn(float2 E, float Roughness)
{
const float PI = 3.14159265f;
float m = Roughness * Roughness;
float n = 2 / max(0.0001, m*m) - 2;

float Phi = 2 * PI * E.x;
float CosTheta = ClampedPow(E.y, 1 / (n + 1));
float SinTheta = Sqrt(1 - CosTheta * CosTheta);

// TODO, TEST : swap y z
float3 H;
H.x = SinTheta * cos(Phi);
/*H.y = SinTheta * sin(Phi);
H.z = CosTheta;*/
H.y = CosTheta;
H.z = SinTheta * sin(Phi);

float D = (n + 2) / (2 * PI) * ClampedPow(CosTheta, n);
float PDF = D * CosTheta;

return float4(H, PDF);
}

float3x3 GetTangentBasis(float3 TangentY)
{
float3 UpVector = abs(TangentY.z) < 0.999 ? float3(0, 1, 0) : float3(0, 0, 1);
float3 TangentX = normalize(cross(UpVector, TangentY));
float3 TangentZ = cross(TangentY, TangentX);
return float3x3(TangentX, TangentY, TangentZ);
}

float3 TangentToWorld(float3 Vec, float3 TangentZ)
{
return mul(Vec, GetTangentBasis(TangentZ));
}

float2 ReprojectHit(PASamplerParam(texVelocity, samVelocity), float4x4 matInvViewOriginProjection, float4x4 matPrevViewOriginProjectionTexScale, float3 HitUVz)
{
const bool useVelocityTexture = true;

if (useVelocityTexture)
{
// zw is pure velocity 
float2 Velocity = PAGetTexelLod(texVelocity, samVelocity, float4(HitUVz.xy, 0.0, 0.0)).zw;
return HitUVz.xy - Velocity;
}

// Camera motion for pixel (in ScreenPos space).
float4 ThisClip = float4((HitUVz.xy - ScreenPositionScaleBias.wz) / ScreenPositionScaleBias.xy, HitUVz.z, 1);
float4 PrevClip = mul(ThisClip, matInvViewOriginProjection * matPrevViewOriginProjectionTexScale);
PrevClip = mul(PrevClip, matPrevViewOriginProjectionTexScale);
return PrevClip.xy;
}

float4 SampleScreenColor(PASamplerParam(texPrevSceneColor, samPrevSceneColorLinear), float2 UV)
{
float4 OutColor;
OutColor.rgb = PAGetTexelLod(texPrevSceneColor, samPrevSceneColorLinear, float4(UV, 0.0f, 0.0f)).rgb;
OutColor.a = 1;

OutColor = max(0.0f, OutColor);

// Off screen masking
float2 ScreenPos = (UV / fDynamicResolution - ScreenPositionScaleBias.wz) / ScreenPositionScaleBias.xy;

// ver1
/*float2 Vignette = saturate(abs(ScreenPos) * 5.0 - 4.0);
OutColor.w *= saturate(1.0 - dot(Vignette, Vignette));*/

// ver2
const float sharpen = 0.7f;
float2 Vignette = saturate((abs(ScreenPos) - sharpen) / (1.0 - sharpen));
OutColor.w *= saturate(1.0 - length(Vignette));

// Transform NaNs to black, transform negative colors to black.
//OutColor.rgb = -min(-OutColor.rgb, 0.0);

return OutColor;
}

float4 SampleDepthTexture(PASamplerParam(texDepth, samDepth), float Level, float4 SampleUV0, float4 SampleUV1)
{ 
float4 SampleDepth;

#if USE_HZB
SampleDepth.x = PAGetTexelLod(texDepth, samDepth, float4(SampleUV0.xy, 0.0, Level));
SampleDepth.y = PAGetTexelLod(texDepth, samDepth, float4(SampleUV0.zw, 0.0, Level));
SampleDepth.z = PAGetTexelLod(texDepth, samDepth, float4(SampleUV1.xy, 0.0, Level));
SampleDepth.w = PAGetTexelLod(texDepth, samDepth, float4(SampleUV1.zw, 0.0, Level));
#else
SampleDepth.x = PAGetTexelLod(texDepth, samDepth, float4(SampleUV0.xy, 0.0, 0.0f));
SampleDepth.y = PAGetTexelLod(texDepth, samDepth, float4(SampleUV0.zw, 0.0, 0.0f));
SampleDepth.z = PAGetTexelLod(texDepth, samDepth, float4(SampleUV1.xy, 0.0, 0.0f));
SampleDepth.w = PAGetTexelLod(texDepth, samDepth, float4(SampleUV1.zw, 0.0, 0.0f));
#endif

return SampleDepth;
}

float ConvertToDeviceZ(float m33, float m43, float scene_depth)
{
return m33 + m43 / (scene_depth * 10.0);
}

void RayCast(
PASamplerParam(texDepth, samDepth), 
const bool isLinearDepth,
row_major float4x4 matViewOrigin,
row_major float4x4 matProjection,
float3 RayOriginTranslatedWorld, 
float3 RayDirection,
float Roughness, 
float ConeAngleWorld, 
float SceneDepth,
int NumSteps, 
float StepOffset,
float Hierachical_Z_Lod_Scale,
out float4 OutHitUVzTime
)
{
// avoid bugs with early returns inside of loops on certain platform compilers.
float4 Result = float4(0, 0, 0, 1);

const float4 RayStartV = mul(float4(RayOriginTranslatedWorld, 1), matViewOrigin);
const float4 RayDirV = mul(float4(RayDirection * SceneDepth, 0), matViewOrigin);
const float4 RayEndV = RayStartV + RayDirV;

const float4 RayStartClip = mul(RayStartV, matProjection);
const float4 RayEndClip = mul(RayEndV, matProjection);

const float3 RayStartScreen = RayStartClip.xyz / RayStartClip.w;
const float3 RayEndScreen = RayEndClip.xyz / RayEndClip.w;

float4 RayDepthClip = RayStartClip + mul(float4(0, 0, SceneDepth, 0), matProjection);
float3 RayDepthScreen = RayDepthClip.xyz / RayDepthClip.w;

float3 RayStepScreen = RayEndScreen - RayStartScreen;

{
// Computes the scale down factor for RayStepScreen required to fit on the X and Y axis in order to clip it in the viewport
const float RayStepScreenInvFactor = 0.5 * length(RayStepScreen.xy);
const float2 AbsRayStepScreen = abs(RayStepScreen.xy);
const float2 S = (AbsRayStepScreen - max(abs(RayStepScreen.xy + RayStartScreen.xy * RayStepScreenInvFactor) - RayStepScreenInvFactor, 0.0f)) / AbsRayStepScreen;

// Rescales RayStepScreen accordingly
const float RayStepFactor = min(S.x, S.y) / RayStepScreenInvFactor;

RayStepScreen *= RayStepFactor;
}

#if USE_HZB
/*float3 RayStartUVz = float3((RayStartScreen.xy * float2(0.5, -0.5) + 0.5) * HZBUvFactorAndInvFactor.xy, RayStartScreen.z);
float3 RayStepUVz = float3(RayStepScreen.xy * float2(0.5, -0.5) * HZBUvFactorAndInvFactor.xy, RayStepScreen.z);*/
#endif

float3 RayStartUVz = float3((RayStartScreen.xy * float2(0.5, -0.5) + 0.5), RayStartScreen.z); 
float3 RayStepUVz = float3(RayStepScreen.xy * float2(0.5, -0.5), RayStepScreen.z);

RayStartUVz.xy *= fDynamicResolution;
RayStepUVz.xy *= fDynamicResolution;

const float Step = 1.0 / NumSteps; 
//const float CompareTolerance = max(abs(RayStepUVz.z), (RayStartScreen.z - RayDepthScreen.z) * 4) * Step;
const float CompareTolerance = max(abs(RayStepUVz.z), abs(RayStartScreen.z - RayDepthScreen.z)) * Step;

float LastDiff = 0;
float Level = 0.0f; // mipmap lod bias

RayStepUVz *= Step;

// normalize
/*float max_value = max(abs(RayStepUVz.x), abs(RayStepUVz.y));
if (max_value < max(invScreenSize.x, invScreenSize.y))
{
RayStepUVz /= max_value;
}*/

float3 RayUVz = RayStartUVz + RayStepUVz * StepOffset;

[loop]
for (int i = 0; i < NumSteps; i += 4)
{
// Vectorized to group fetches
float4 SampleUV0 = RayUVz.xyxy + RayStepUVz.xyxy * float4(1, 1, 2, 2);
float4 SampleUV1 = RayUVz.xyxy + RayStepUVz.xyxy * float4(3, 3, 4, 4);
float4 SampleZ = RayUVz.zzzz + RayStepUVz.zzzz * float4(1, 2, 3, 4);

// Use lower res for farther samples
float4 SampleDepth = SampleDepthTexture(PASamplerParamToFunc(texDepth, samDepth), Level, SampleUV0, SampleUV1);

// linear depth to device z
#ifndef USE_DEPTH_READ_ONLY_FLAG
if (isLinearDepth)
{
SampleDepth.x = ConvertToDeviceZ(matProjection._33, matProjection._43, SampleDepth.x);
SampleDepth.y = ConvertToDeviceZ(matProjection._33, matProjection._43, SampleDepth.y);
SampleDepth.z = ConvertToDeviceZ(matProjection._33, matProjection._43, SampleDepth.z);
SampleDepth.w = ConvertToDeviceZ(matProjection._33, matProjection._43, SampleDepth.w);
}
#endif
float4 DepthDiff = SampleZ - SampleDepth;

bool4 Hit = abs(DepthDiff - CompareTolerance) < CompareTolerance;

[branch]
// Sky Clipping 버전
// if (any(Hit) && all(SampleDepth < 1.0))
if (any(Hit))
{
float DepthDiff0 = DepthDiff[2];
float DepthDiff1 = DepthDiff[3];
float MinTime = 3;

[flatten] if (Hit[2])
{
DepthDiff0 = DepthDiff[1];
DepthDiff1 = DepthDiff[2];
MinTime = 2;
}
[flatten] if (Hit[1])
{
DepthDiff0 = DepthDiff[0];
DepthDiff1 = DepthDiff[1];
MinTime = 1;
}
[flatten] if (Hit[0])
{
DepthDiff0 = LastDiff;
DepthDiff1 = DepthDiff[0];
MinTime = 0;
}

// Find more accurate hit using line segment intersection
float TimeLerp = saturate(DepthDiff0 / (DepthDiff0 - DepthDiff1));
float IntersectTime = MinTime + TimeLerp;
float3 HitUVz = RayUVz + RayStepUVz * IntersectTime;

Result = float4(HitUVz, 0.5);
break;
}

LastDiff = DepthDiff.w;
Level += Hierachical_Z_Lod_Scale / NumSteps;
RayStepUVz += RayStepUVz * Hierachical_Z_Lod_Scale;
RayUVz += 4 * RayStepUVz;

if (SampleUV1.z < 0.0f || 1.0f < SampleUV1.z || SampleUV1.w < 0.0f || 1.0f < SampleUV1.w)
{
break;
}
}

#if USE_HZB
//Result.xy *= HZBUvFactorAndInvFactor.zw;
#endif

OutHitUVzTime = Result;
}



float4 getSSReflectionUltra(PASamplerParam(texDepth, samDepth), const bool isLinearDepth, PASamplerParam(texDiffuse, samDiffuse),
float4x4 matViewOrigin, float4x4 matProjection, float3 relWorldPos, float3 vecNormal, float Roughness, float2 UV, int2 PixelPos)
{
float4 OutColor = 0;
float SceneDepth = length(relWorldPos);
float3 V = -(relWorldPos / SceneDepth);

const float distance_threshold = 50000.0f;

float angle = saturate(dot(vecNormal.xyz, V));

// 카메라가 천정이나 바닥을 볼때에는 angle cut을 완화시켜 준다.
const float angle_threshold = saturate(0.75f + (1.0 - matViewOrigin._22));
float distance_fade = 1.0f - saturate(SceneDepth / distance_threshold);

float fade = saturate(distance_fade * (angle_threshold - angle) * 100.0);

[branch]
if (angle_threshold <= angle)
{
return OutColor;
}

const bool useJitter = false;
const float StateFrameIndexMod8 = 0.0f; // useJitter ? frameCount : 0.0f;
float FrameRandom = StateFrameIndexMod8 * 1551.0f;

float2 HitSampleUV = float2(-1.0, -1.0); 
const float Hierachical_Z_Lod_Scale = 1.0f;

//float quality = distance_fade * distance_fade * distance_fade;
int NumSteps = 4;// lerp(3, 6, quality);

uint2 Random = PseudoRandom(PixelPos.xy + StateFrameIndexMod8 * float2(97, 71)) * uint2(12, 25);
Random *= uint2(0x3127352, 0x11229256);
// Sample set dithered over 4x4 pixels
uint Morton = MortonCode(PixelPos.x & 3) | (MortonCode(PixelPos.y & 3) * 2);
uint PixelIndex = ReverseUIntBits(Morton);
uint Offset = (PixelIndex + ReverseUIntBits(FrameRandom + 117)) & 15;
float StepOffset = Offset / 15.0;
StepOffset *= -0.1f;
float2 E = Hammersley(0, 1, Random);
float3 H = TangentToWorld(ImportanceSampleBlinn(E, 0.1f).xyz, vecNormal.xyz);
float3 R = 2 * dot(V, H) * H - V;

float4 HitUVzTime;

RayCast(
PASamplerParamToFunc(texDepth, samDepth),
isLinearDepth,
matViewOrigin,
matProjection,
relWorldPos,
R,
Roughness,
0.001,
SceneDepth,
NumSteps,
StepOffset,
Hierachical_Z_Lod_Scale,
HitUVzTime
);

// if there was a hit
[branch]
if (HitUVzTime.w < 1)
{
// no reproject..
OutColor = SampleScreenColor(PASamplerParamToFunc(texDiffuse, samDiffuse), HitUVzTime.xy);
OutColor.xyz = min(10.0f, OutColor.xyz);
}
return OutColor;
}