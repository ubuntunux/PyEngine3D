float4 SimpleTAA_PixelShader(FullSceneQuadSimpleVS_Output input) : PA_PS_OUTPUT
{
float2 uv = input.Tex;
float4 sum = 0.0f;
float totalWeight = 0.0f;

float4 clrMin = 99999999.0f;
float4 clrMax = -99999999.0f;

float4 m1 = 0.0f;
float4 m2 = 0.0f;
float mWeight = 0.0f;

const int SampleRadius_ = 1;
const float filterRadius = ResolveFilterDiameter / 2.0f;

[loop]
for (int y = -SampleRadius_; y <= SampleRadius_; ++y)
{
[loop]
for (int x = -SampleRadius_; x <= SampleRadius_; ++x)
{
float2 sampleOffset = float2(x, y);
float2 sampleUV = saturate(uv + sampleOffset / screenSize);
float4 sampleColor = PAGetTexelLod(InputTexture, samInputTexture, float4(sampleUV, 0.0f, 0.0f));
float2 sampleDist = abs(sampleOffset) / (ResolveFilterDiameter / 2.0f);
float weight = Filter(sampleDist.x, ResolveFilterType, filterRadius, true) * Filter(sampleDist.y, ResolveFilterType, filterRadius, true);
clrMin = min(clrMin, sampleColor);
clrMax = max(clrMax, sampleColor);

// InverseLuminanceFiltering
weight *= 1.0f / (1.0f + Luminance(sampleColor.xyz));
sum += sampleColor * weight;
totalWeight += weight;

m1 += sampleColor;
m2 += sampleColor * sampleColor;
mWeight += 1.0f;
}
}

float4 output = PAGetTexelLod(InputTexture, samInputTexture, float4(uv, 0.0f, 0.0f));

// Anti Aliasing
float4 currColor = output;
float2 velocity = PAGetTexelLod(VelocityTexture, samVelocityTexture, float4(uv / velocityDynamicResolution, 0.0, 0.0)).xy * velocityDynamicResolution;
float4 prevColor = PAGetTexelLod(PrevFrameTexture, samPrevFrameTexture, float4((uv - velocity) * fDynamicResolutionPrev / fDynamicResolution, 0.0f, 0.0f));

if (NeighborhoodClampMode == ClampModes_RGB_Clamp)
{
prevColor = clamp(prevColor, clrMin, clrMax);
}
else if (NeighborhoodClampMode == ClampModes_RGB_Clip)
{
prevColor = ClipAABB(clrMin, clrMax, prevColor, m1 / mWeight);
}
else if (NeighborhoodClampMode == ClampModes_Variance_Clip)
{
float4 mu = m1 / mWeight;
float4 sigma = sqrt(abs(m2 / mWeight - mu * mu));
float4 minc = mu - VarianceClipGamma * sigma;
float4 maxc = mu + VarianceClipGamma * sigma;
prevColor = ClipAABB(minc, maxc, prevColor, mu);
}

// Color, Alpha값 차이에 따라 부드럽게 보간
float4 weightB = lerp(0.9f, 0.99f, saturate(abs(clrMax - clrMin) / currColor));
float4 weightA = 1.0f - weightB;

// InverseLuminanceFiltering)
weightA = weightA / (1.0f + Luminance(currColor.xyz));
weightB = weightB / (1.0f + Luminance(prevColor.xyz));

weightA = weightA * (1.0 + currColor.w * 10.0f);
weightB = weightB * (1.0f + prevColor.w * 10.0f);

output = (currColor * weightA + prevColor * weightB) / (weightA + weightB);

return output;
}