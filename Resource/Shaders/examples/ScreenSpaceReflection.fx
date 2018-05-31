#include "Encode.fx"
#include "D3DDefine.fx"
#include "ShadowFunction.fx"
#include "OutdoorScattering.fx"
#include "ScreenSpaceRayCast.fxh"


CBUFFER_START(reflectConst)
row_major float4x4 matViewOrigin;
row_major float4x4 matProjection;
row_major float4x4 matInvViewOriginProjection;
row_major float4x4 matViewOriginProjectionTexScale;
row_major float4x4 matPrevViewOriginProjectionTexScale; 
float4 HZBUvFactorAndInvFactor;

int frameCount;
float2 invScreenSize;
float _dummy0;
CBUFFER_END


PATexture2D(texPrevSceneColor);
PASampler2D(texPrevSceneColor, samPrevSceneColorLinear, PA_LINEAR_CLAMP_FILTER);

PATexture2D(texDepthRaw);
PASampler2D(texDepthRaw, samDepthRaw, PA_POINT_CLAMP_FILTER);

PATexture2D(texDepthSmall);
PASampler2D(texDepthSmall, samDepthSmall, PA_POINT_CLAMP_FILTER);

PATexture2D(texDiffuse);
PASampler2D(texDiffuse, samDiffuse, PA_POINT_CLAMP_FILTER);

PATexture2D(texVertexNormal);
PASampler2D(texVertexNormal, samVertexNormal, PA_LINEAR_CLAMP_FILTER);

PATexture2D(texNormal);
PASampler2D(texNormal, samNormal, PA_POINT_CLAMP_FILTER);
PASampler2D(texNormal, samNormalLinear, PA_LINEAR_CLAMP_FILTER);

PATexture2D(texVelocity);
PASampler2D(texVelocity, samVelocity, PA_POINT_CLAMP_FILTER);

PATexture2D(texNoise);
PASampler2D(texNoise, samNoise, PA_LINEAR_WRAP_FILTER);

PATexture2D(texRainPool);
PASampler2D(texRainPool, samRainPool, PA_LINEAR_CLAMP_FILTER);


float4 SceneReflectPixelShaderUltra(FullSceneQuadVS_Output input, float4 screenTex :PA_PS_VPOS) : PA_PS_OUTPUT0
{
float4 OutColor = 0;
float2 UV = input.Tex.xy; // Texture Coordinate
float2 ScreenPos = UV * float2(2, -2) + float2(-1, 1); // NDC Coordinate
int2 PixelPos = (int2)screenTex.xy; // Screen Pixel Coordinate

// ==============================================================
// World Position & Depth
// ==============================================================
// Depth raw version
/*float fDepthRaw = PAGetTexel(texDepthRaw, samDepthRaw, UV).x;
float4 vecWorldPosition = float4(ScreenPos, fDepthRaw, 1.0f);
vecWorldPosition = mul(vecWorldPosition, matInvViewOriginProjection);
vecWorldPosition /= vecWorldPosition.w;
float fDepth = length(vecWorldPosition.xyz);
float3 V = normalize(-vecWorldPosition.xyz);*/

// linear depth version
float3 V = normalize(-input.Direction);
float fDepth = PAGetTexel(texDepthSmall, samDepthSmall, UV).x * 10.0;
float3 vecWorldPosition = -V * fDepth;

const float distance_threshold = 50000.0f;

[branch]
if (distance_threshold <= fDepth)
{
return float4(OutColor.xyz, 1.0);
}

// ==============================================================
// Decode Deferred
// ==============================================================
float4 vecDiffuse = 0.0f;
float4 vecDiffuseRaw = 0.0f;
float4 vecMaterial = 0.0f;
float4 vecNormal = 1.0f;
float3 vecVertexNormal = 0.0;
float4 vecNormalRaw = 1.0f; 
int materialID = 0;
bool isFixture = false;

// SSR의 렌더타겟은 GBuffer보다 작으므로 텍셀가져올때 주의 할것!
float2 fixed_pixel_pos = floor(UV.xy / invScreenSize.xy);
float2 fixed_uv = (fixed_pixel_pos + 0.5f) * invScreenSize.xy;
#if defined(DX11) && defined(USE_REMASTER) 
decodeDeferredUltra(fixed_uv, fixed_pixel_pos, 0.0f, invScreenSize.xy, PASamplerParamToFunc(texDiffuse, samDiffuse), PASamplerParamToFunc(texNormal, samNormal), PASamplerParamToFunc(texVertexNormal, samVertexNormal), PASamplerParamToFunc(texDepthRaw, samDepthRaw), vecDiffuse, vecDiffuseRaw, vecNormal, vecVertexNormal, vecMaterial, vecNormalRaw, materialID, isFixture);
#else
decodeDeferred2(fixed_uv, fixed_pixel_pos, 0.0f, invScreenSize.xy, PASamplerParamToFunc(texDiffuse, samDiffuse), PASamplerParamToFunc(texNormal, samNormal), PASamplerParamToFunc(texDepthRaw, samDepthRaw), vecDiffuse, vecDiffuseRaw, vecNormal, vecVertexNormal, vecMaterial, vecNormalRaw, materialID);
#endif

[branch]
if (materialID == ENCODE_TYPE_GRASS ||
materialID == ENCODE_TYPE_LEAVES ||
materialID == ENCODE_TYPE_TRUNK)
{
return float4(OutColor.xyz, 1.0);
}

float wetRate = PAGetTexelLod(texRainPool, samRainPool, float4(input.Tex, 0, 0)).w;
float Roughness = lerp(saturate(1.0 - vecMaterial.y * vecMaterial.y), 0.0f, saturate(wetRate * 2.0f));
vecNormal.xyz = lerp(vecNormal.xyz, vecVertexNormal.xyz, wetRate * 0.75f);

// 노말정밀도오류 및 비오는 날 처리를 위해, 보정을 해줌
vecNormal.y += pow(vecNormal.y, 2) * 1.5f;
vecNormal.xyz = normalize(vecNormal.xyz);

float angle = saturate(dot(vecNormal.xyz, V));

// 카메라가 천정이나 바닥을 볼때에는 angle cut을 완화시켜 준다.
const float angle_threshold = saturate(0.75f + (1.0 - matViewOrigin._22)); 
float distance_fade = 1.0f - saturate(fDepth / distance_threshold);

float fade = saturate(distance_fade * (angle_threshold - angle) * 100.0);

[branch]
if (angle_threshold <= angle || fade <= 0.0f)
{
return float4(OutColor.xyz, 1.0);
}

const bool useJitter = true;
const float StateFrameIndexMod8 = useJitter ? frameCount : 0.0f;
const float FrameRandom = StateFrameIndexMod8 * 1551.0f;

float quality = distance_fade * distance_fade * distance_fade;

const float Hierachical_Z_Lod_Scale = (lerp(4.0f, 0.0f, quality) + Roughness);
const float random_scale = lerp(0.01f, 0.7f, saturate(Roughness));

int NumSteps = lerp(1, 8, quality);// *saturate(1.0 - Roughness * 0.5f));
int NumRays = lerp(2, 6, quality);// *saturate(Roughness + 0.5f));

//#define SSR_QUALITY 5
//#if SSR_QUALITY == 1
// const int NumSteps = 8;
// const int NumRays = 1;
//#elif SSR_QUALITY == 2
// const int NumSteps = 16;
// const int NumRays = 1;
//#elif SSR_QUALITY == 3
// const int NumSteps = 8;
// const int NumRays = 8;
//#elif SSR_QUALITY == 4
// const int NumSteps = 10;
// const int NumRays = 8;
//#else // SSR_QUALITY == 5
// const int NumSteps = 12;
// const int NumRays = 12;
//#endif

float2 HitSampleUV = float2(-1.0, -1.0);

[branch]
if( NumRays > 1 )
{
#define SSR_OPTIMIZED 0
#if SSR_OPTIMIZED != 1
uint2 Random = PseudoRandom(PixelPos.xy + StateFrameIndexMod8 * float2(97, 71)) * uint2(12, 25);
Random *= uint2(0x3127352, 0x11229256);

// Sample set dithered over 4x4 pixels
uint Morton = MortonCode(PixelPos.x & 3) | (MortonCode(PixelPos.y & 3) * 2);
uint PixelIndex = ReverseUIntBits(Morton);
#endif
float hitCount = 0.0f;

// Shoot multiple rays
[loop]
for (int i = 0; i < NumRays; i++)
{
#if SSR_OPTIMIZED
float StepOffset = PseudoRandom(screenTex.xy + (i + StateFrameIndexMod8) * 3.141592);
float2 E = normalize(float3(sin(StepOffset * 3.141592), 1.0f, cos(StepOffset * 3.141592)));
#else
uint Offset = (PixelIndex + ReverseUIntBits(FrameRandom + i * 117)) & 15;
float StepOffset = Offset / 15.0;
StepOffset -= 0.5;
float2 E = Hammersley(i, NumRays, Random);
#endif
float3 H = TangentToWorld(ImportanceSampleBlinn(E, random_scale).xyz, vecNormal.xyz);
float3 R = 2 * dot(V, H) * H - V;
R.y *= 0.9f; // 좀더 길게

float4 HitUVzTime;

RayCast(
PASamplerParamToFunc(texDepthSmall, samDepthSmall), 
true,
matViewOrigin, 
matProjection,
vecWorldPosition.xyz,
R,
Roughness,
0.001,
fDepth,
NumSteps,
StepOffset,
Hierachical_Z_Lod_Scale,
HitUVzTime
);

// if there was a hit
[branch]
if (HitUVzTime.w < 1)
{
HitSampleUV = ReprojectHit(PASamplerParamToFunc(texVelocity, samVelocity), matInvViewOriginProjection, matPrevViewOriginProjectionTexScale, HitUVzTime.xyz);
HitSampleUV = HitSampleUV * fDynamicResolutionPrev / fDynamicResolution;
float4 SampleColor = SampleScreenColor(PASamplerParamToFunc(texPrevSceneColor, samPrevSceneColorLinear), HitSampleUV);
SampleColor.rgb /= 1 + Luminance(SampleColor.rgb);
OutColor.rgb += SampleColor.xyz;
hitCount += 1.0f;
}
}

if (0.0f < hitCount)
{
OutColor.rgb /= hitCount; 
OutColor.rgb /= 1 + Luminance(OutColor.rgb);
OutColor.a = hitCount / NumRays;
}
}
else
{
float StepOffset = InterleavedGradientNoise(screenTex.xy, StateFrameIndexMod8);

float3 R = reflect(-V, vecNormal.xyz );
R.y *= 0.9f; // 좀더 길게

float4 HitUVzTime;

RayCast(
PASamplerParamToFunc(texDepthSmall, samDepthSmall),
true,
matViewOrigin,
matProjection,
vecWorldPosition.xyz,
R,
Roughness,
0.001,
fDepth,
NumSteps,
StepOffset,
Hierachical_Z_Lod_Scale,
HitUVzTime
);

// if there was a hit
[branch]
if (HitUVzTime.w < 1)
{
HitSampleUV = ReprojectHit(PASamplerParamToFunc(texVelocity, samVelocity), matInvViewOriginProjection, matPrevViewOriginProjectionTexScale, HitUVzTime.xyz );
HitSampleUV = HitSampleUV * fDynamicResolutionPrev / fDynamicResolution;
OutColor = SampleScreenColor(PASamplerParamToFunc(texPrevSceneColor, samPrevSceneColorLinear), HitSampleUV);
}
}
OutColor.xyz = min(10.0f, OutColor.xyz);
OutColor.w *= fade;

return OutColor;
}


float4 SceneReflectPixelShader(FullSceneQuadVS_Output input, float4 screenTex :PA_PS_VPOS, uniform int nRenderMode) : PA_PS_OUTPUT0
{
const bool isHighQuality = (nRenderMode == 0);

if (!isHighQuality)
{
[branch]
if (frameCount % 2 == 1 && screenTex.x % 2 < 1)
discard;
else if (frameCount % 2 == 0 && screenTex.x % 2 >= 1)
discard;
}

float fDepthNormalInfo = PAGetTexel(texDepthSmall, samDepthSmall, input.Tex).x * 10.0f;
const float clipDistance = 7000.0f;
[branch] if (clipDistance < fDepthNormalInfo) return 0;

float3 vecViewDirection = normalize(input.Direction);
float3 vecWorldPos = vecViewDirection * fDepthNormalInfo;

int materialID;
float3 vecNormal = decodeSmallNormal(PAGetTexel(texNormal, samNormalLinear, input.Tex), materialID);
vecNormal.y += pow(vecNormal.y, 2) * 1.5f; // 노말정밀도오류 및 비오는 날 처리를 위해, 보정을 해줌
vecNormal = normalize(vecNormal);

float3 vecReflect = normalize(reflect(vecViewDirection, vecNormal));
vecReflect.y *= 0.9f; // 좀더 길게

float fNoise = PAGetTexelLod(texNoise, samNoise, float4(input.Tex * 20.0f,0,0)).y;

// ================================================
// Quality Control
// ================================================
float offset = 20.0f;
float DIST_MUL = 0.05f;
float OFFSET_MUL = lerp(1.1f, 1.5f, fDepthNormalInfo / 1000.0f);
int ITER0_COUNT = 6;
int ITER1_COUNT = 3;
if (isHighQuality)
{
ITER0_COUNT = 8; // ITER1에 비해 ITER0을 작게하는게 최적화에 좋을듯
ITER1_COUNT = 5;
}

// ================================================
{
const float noiseRate = 0.25f;
offset *= lerp(1.0f, fNoise, noiseRate);
offset += fDepthNormalInfo * DIST_MUL;
}

float isChecked = 0.0f;
float isCheckedSky = 0.0f;
float3 vecViewSpaceRandomPosition = vecWorldPos;
float hitRate = 1.0f;

[loop]
for (int i = 0; i < ITER0_COUNT; i++)
{
vecViewSpaceRandomPosition += vecReflect * offset;

float4 vecTransSamplePosition = mul(float4(vecViewSpaceRandomPosition, 1.0f), matViewOriginProjectionTexScale);
float2 vecTrans2DSamplePosition = vecTransSamplePosition.xy / vecTransSamplePosition.w;

if (vecTrans2DSamplePosition.x < 0.0f || vecTrans2DSamplePosition.x > 1.0f ||
vecTrans2DSamplePosition.y < 0.0f || vecTrans2DSamplePosition.y > 1.0f)
break;


float fDepth = PAGetTexelLod(texDepthSmall, samDepthSmall, float4(vecTrans2DSamplePosition,0,0)).x * 10.0f;
float fDistance = length(vecViewSpaceRandomPosition);

[flatten]
if (fDistance > fDepth && fDepthNormalInfo < fDepth)
{
isChecked += 1.05f;
}
else if (fDepth > 50000.0f)
{
isCheckedSky += 0.55f;
}
else
{
hitRate -= 1.0f / (float)ITER0_COUNT;
}

[branch] if (isChecked >= 1.0f || isCheckedSky >= 1.0f) break;

offset *= OFFSET_MUL; // for next
}

// Reverse Iteration
[branch]
if (isChecked >= 1.0f)
{
offset = -offset * 0.5f;

[loop]
for (int i = 0; i < ITER1_COUNT; i++)
{
vecViewSpaceRandomPosition += vecReflect * offset;

float4 vecTransSamplePosition = mul(float4(vecViewSpaceRandomPosition, 1.0f), matViewOriginProjectionTexScale);
float2 vecTrans2DSamplePosition = vecTransSamplePosition.xy / vecTransSamplePosition.w;

float transZ = length(vecViewSpaceRandomPosition);
float sampledDepth = PAGetTexelLod(texDepthSmall, samDepthSmall, float4(vecTrans2DSamplePosition,0,0)).x * 10.0f;

[flatten]
if (sampledDepth < transZ)
offset = -abs(offset) * 0.5f;
else
offset = +abs(offset) * 0.5f;
}
}

// Color Sampling
float4 result = 0.0f;
{
float4 vecTransSamplePosition = mul(float4(vecViewSpaceRandomPosition, 1.0f), matPrevViewOriginProjectionTexScale);
float2 vecTrans2DSamplePosition = vecTransSamplePosition.xy / vecTransSamplePosition.w;

if (isHighQuality)
{
const float2 bias = invScreenSize.xy * 0.5f;

result.xyz = PAGetTexelLod(texPrevSceneColor, samPrevSceneColorLinear, float4(vecTrans2DSamplePosition + float2(bias.x, bias.y),0,0));
result.xyz += PAGetTexelLod(texPrevSceneColor, samPrevSceneColorLinear, float4(vecTrans2DSamplePosition + float2(-bias.x,-bias.y),0,0));
result.xyz += PAGetTexelLod(texPrevSceneColor, samPrevSceneColorLinear, float4(vecTrans2DSamplePosition + float2(bias.x,-bias.y),0,0));
result.xyz += PAGetTexelLod(texPrevSceneColor, samPrevSceneColorLinear, float4(vecTrans2DSamplePosition + float2(-bias.x, bias.y),0,0));
result.xyz /= 4.0f;
}
else
{
result.xyz = PAGetTexelLod(texPrevSceneColor, samPrevSceneColorLinear, float4(vecTrans2DSamplePosition,0,0));
}

[branch]
if (hitRate > 0.01f)
{
result.w = saturate(pow(hitRate * 1.5f, 0.75));

// 화면끝 stretch 방지
float2 edgeFade = saturate(1.0f - pow(abs(vecTrans2DSamplePosition.xy - 0.5f) * 2.0f, 2.0f));
result.w *= edgeFade.x * edgeFade.y;

float distanceFade = 1.0f - saturate((fDepthNormalInfo - clipDistance + 2000.0f) / 2000.0f);
result.w *= distanceFade;
}
}

float mulDiscardColor = 0.5f;
[flatten] if (isChecked + isCheckedSky < 1.0f) result *= float4(mulDiscardColor, mulDiscardColor, mulDiscardColor, 0.0f);

result.xyz = pow(result.xyz, 0.8f) * 0.9f;


return result;
}

PA_technique GenerateSceneReflect
{
#ifdef DX11
// High Quality
pass P0
{
PA_DISABLEDEPTH;
PA_ALPHABLEND_DISABLE;

PA_FullSceneQuad
CompilePS(SceneReflectPixelShader(0));
}

// interlaced, low Quality 
pass P1
{
PA_DISABLEDEPTH;
PA_ALPHABLEND_DISABLE;

PA_FullSceneQuad
CompilePS(SceneReflectPixelShader(1));
}

// Ultra Quality
pass P2
{

PA_DISABLEDEPTH;
PA_ALPHABLEND_DISABLE;

PA_FullSceneQuad
CompilePS(SceneReflectPixelShaderUltra());
}
#endif // DX11
}