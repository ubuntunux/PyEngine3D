//--------------------------------------------------------------------------------------
// Tessellation
//--------------------------------------------------------------------------------------
#define TESSELLATION_FLAT 0
#define TESSELLATION_PN_TRIANGLE 1
#define TESSELLATION_PHONG 2
//#define TESSELLATION_TYPE TESSELLATION_PN_TRIANGLE
 
int tessellation_type = TESSELLATION_PN_TRIANGLE;
float tessellation_factor = 8.0f;
float tessellation_height = 15.0f;
float2 texParallaxInvSize;
 
//--------------------------------------------------------------------------------------
// Hull shader
//--------------------------------------------------------------------------------------
struct HS_CONSTANT_DATA_OUTPUT
{
    float    Edges[3]         : SV_TessFactor;
    float    Inside : SV_InsideTessFactor;
    //float    VertexDensity[3] : VERTEX_DENSITY;
    //#if TESSELLATION_PN_TRIANGLE == TESSELLATION_TYPE
    float3  b210 : TEXCOORD0;
    float3  b120 : TEXCOORD1;
    float3  b021 : TEXCOORD2;
    float3  b012 : TEXCOORD3;
    float3  b102 : TEXCOORD4;
    float3  b201 : TEXCOORD5;
    float3  b111 : TEXCOORD6;
    float3  n110 : TEXCOORD7;
    float3  n011 : TEXCOORD8;
    float3  n101 : TEXCOORD9;
    //#endif
};
 
HS_CONSTANT_DATA_OUTPUT CharacterDefer_ConstantsHS(InputPatch<CHARACTER_DEFER_VS_OUTPUT, 3> inputPatch, uint PatchID : SV_PrimitiveID)
{
    HS_CONSTANT_DATA_OUTPUT output = (HS_CONSTANT_DATA_OUTPUT)0;
    float3 vFactor = float3(1.0, 1.0, 1.0);
    float3 vDistance = float3(1.0, 1.0, 1.0);
 
    {
        float2 screenPos0 = inputPatch[0].m_vecPosition.xy / inputPatch[0].m_vecPosition.w;
        float2 screenPos1 = inputPatch[1].m_vecPosition.xy / inputPatch[1].m_vecPosition.w;
        float2 screenPos2 = inputPatch[2].m_vecPosition.xy / inputPatch[2].m_vecPosition.w;
 
        // Set tessellation factor to 0 if the whole triangle patch is outside the view frustum
        float4 min_max;
        min_max.xy = min(screenPos0, min(screenPos1, screenPos2));
        min_max.zw = max(screenPos0, max(screenPos1, screenPos2));
        [branch]
        if (min_max.x > 1.0 || min_max.y > 1.0 || min_max.z < -1.0 || min_max.w < -1.0)
        {
            output.Edges[0] = 0.0;
            output.Edges[1] = 0.0;
            output.Edges[2] = 0.0;
            output.Inside = 0.0;
            return output;
        }
    }
 
    float3 edge0 = (inputPatch[2].m_vecWorldPosition.xyz + inputPatch[1].m_vecWorldPosition.xyz) * 0.5;
    float3 edge1 = (inputPatch[2].m_vecWorldPosition.xyz + inputPatch[0].m_vecWorldPosition.xyz) * 0.5;
    float3 edge2 = (inputPatch[0].m_vecWorldPosition.xyz + inputPatch[1].m_vecWorldPosition.xyz) * 0.5;
 
    //if( inputPatch[0].m_vecStatus.z == 0.f )
    {
        // distance lod
        /*const float minDist = 500.0;
        const float maxDist = 50000.0;
        vDistance.x = length(vecViewPosition.xyz - edge0);
        vDistance.y = length(vecViewPosition.xyz - edge1);
        vDistance.z = length(vecViewPosition.xyz - edge2);
        vFactor = max(vFactor, lerp(tessellation_factor, 1.0f, saturate((vDistance.x-minDist)/(maxDist-minDist))));*/
        vFactor = float3(tessellation_factor, tessellation_factor, tessellation_factor);
    }
 
    // TODO : Orientation-Adaptive Tessellation
 
    // Assign tessellation levels
    output.Edges[0] = vFactor.x;
    output.Edges[1] = vFactor.y;
    output.Edges[2] = vFactor.z;
    output.Inside = (vFactor.x + vFactor.y + vFactor.z) * 0.3333f;
 
    // // PN Triangle Tessellation - compute tessellation control points
    [branch]
    if (TESSELLATION_PN_TRIANGLE == tessellation_type)
    {
        const float3 P0 = inputPatch[0].m_vecWorldPosition.xyz;
        const float3 P1 = inputPatch[1].m_vecWorldPosition.xyz;
        const float3 P2 = inputPatch[2].m_vecWorldPosition.xyz;
        const float3 N0 = inputPatch[0].m_vecNormal;
        const float3 N1 = inputPatch[1].m_vecNormal;
        const float3 N2 = inputPatch[2].m_vecNormal;
 
        // compute control points
        output.b210 = (2.0*P0 + P1 - dot(P1 - P0, N0) * N0) / 3.0;
        output.b120 = (2.0*P1 + P0 - dot(P0 - P1, N1) * N1) / 3.0;
        output.b021 = (2.0*P1 + P2 - dot(P2 - P1, N1) * N1) / 3.0;
        output.b012 = (2.0*P2 + P1 - dot(P1 - P2, N2) * N2) / 3.0;
        output.b102 = (2.0*P2 + P0 - dot(P0 - P2, N2) * N2) / 3.0;
        output.b201 = (2.0*P0 + P2 - dot(P2 - P0, N0) * N0) / 3.0;
        float3 E = (output.b210
            + output.b120
            + output.b021
            + output.b012
            + output.b102
            + output.b201) / 6.0;
        float3 V = (P0 + P1 + P2) / 3.0;
        output.b111 = E + (E - V)*0.5;
        output.n110 = normalize(N0 + N1 - vij(N0, P0, N1, P1)*(P1 - P0));
        output.n011 = normalize(N1 + N2 - vij(N1, P1, N2, P2)*(P2 - P1));
        output.n101 = normalize(N2 + N0 - vij(N2, P2, N0, P0)*(P0 - P2));
    }
 
    return output;
}
 
 
 
[domain("tri")]
[partitioning("integer")]
[outputtopology("triangle_cw")]
[outputcontrolpoints(3)]
[patchconstantfunc("CharacterDefer_ConstantsHS")]
[maxtessfactor(64.0)]
CHARACTER_DEFER_VS_OUTPUT CharacterSceneDefer_HS(InputPatch<CHARACTER_DEFER_VS_OUTPUT, 3> inputPatch, in uint uCPID : SV_OutputControlPointID)
{
    return inputPatch[uCPID];
}
 
//--------------------------------------------------------------------------------------
// Domain Shader
//--------------------------------------------------------------------------------------
[domain("tri")]
CHARACTER_DEFER_VS_OUTPUT CharacterSceneDefer_DS(HS_CONSTANT_DATA_OUTPUT input, float3 uvw : SV_DomainLocation,
    const OutputPatch<CHARACTER_DEFER_VS_OUTPUT, 3> TrianglePatch)
{
    CHARACTER_DEFER_VS_OUTPUT output = (CHARACTER_DEFER_VS_OUTPUT)0;
 
    // Interpolate other inputs with barycentric coordinates
    output.m_vecTangentU = uvw.x * TrianglePatch[0].m_vecTangentU +
        uvw.y * TrianglePatch[1].m_vecTangentU +
        uvw.z * TrianglePatch[2].m_vecTangentU;
 
    output.m_vecTangentV = uvw.x * TrianglePatch[0].m_vecTangentV +
        uvw.y * TrianglePatch[1].m_vecTangentV +
        uvw.z * TrianglePatch[2].m_vecTangentV;
 
    [branch]
    if (TESSELLATION_FLAT == tessellation_type)
    {
        // Interpolate world space normal and renormalize it
        output.m_vecNormal = normalize(uvw.x * TrianglePatch[0].m_vecNormal +
            uvw.y * TrianglePatch[1].m_vecNormal +
            uvw.z * TrianglePatch[2].m_vecNormal);
 
        output.m_vecWorldPosition = uvw.x * TrianglePatch[0].m_vecWorldPosition +
            uvw.y * TrianglePatch[1].m_vecWorldPosition +
            uvw.z * TrianglePatch[2].m_vecWorldPosition;
    }
    else if (TESSELLATION_PN_TRIANGLE == tessellation_type)
    {
        float3 uvwSquared = uvw * uvw;
        float3 uvwCubed = uvwSquared * uvw;
 
        // compute PN normal
        output.m_vecNormal = normalize(TrianglePatch[0].m_vecNormal * uvwSquared.x
            + TrianglePatch[1].m_vecNormal * uvwSquared.y
            + TrianglePatch[2].m_vecNormal * uvwSquared.z
            + input.n110 * uvw.x * uvw.y
            + input.n011 * uvw.y * uvw.z
            + input.n101 * uvw.x * uvw.z);
 
        // recompute tangent vectors
        float3 tangentU = cross(output.m_vecTangentV.xyz, output.m_vecNormal);
        output.m_vecTangentV.xyz = cross(output.m_vecNormal, tangentU);
        // flip ( UV를 겹쳐쓰는경우 탄젠트가 반대일수 있기 때문에 뒤집어 준다. )
        output.m_vecTangentU.xyz = dot(tangentU, output.m_vecTangentU.xyz) > 0.0 ? tangentU : -tangentU;
 
        // compute PN position
        output.m_vecWorldPosition.xyz = TrianglePatch[0].m_vecWorldPosition.xyz * uvwCubed.x
            + TrianglePatch[1].m_vecWorldPosition.xyz * uvwCubed.y
            + TrianglePatch[2].m_vecWorldPosition.xyz * uvwCubed.z
            + input.b210 * uvwSquared.x * uvw.y * 3.0
            + input.b120 * uvwSquared.y * uvw.x * 3.0
            + input.b201 * uvwSquared.x * uvw.z * 3.0
            + input.b021 * uvwSquared.y * uvw.z * 3.0
            + input.b102 * uvwSquared.z * uvw.x * 3.0
            + input.b012 * uvwSquared.z * uvw.y * 3.0
            + input.b111 * 6.0 * uvw.x * uvw.y * uvw.z;
        output.m_vecWorldPosition.w = uvw.x * TrianglePatch[0].m_vecWorldPosition.w +
            uvw.y * TrianglePatch[1].m_vecWorldPosition.w +
            uvw.z * TrianglePatch[2].m_vecWorldPosition.w;
    }
    else // TESSELLATION_PHONG
    {
        float3 uvwSquared = uvw * uvw;
 
        // Interpolate world space normal and renormalize it
        output.m_vecNormal = normalize(uvw.x * TrianglePatch[0].m_vecNormal +
            uvw.y * TrianglePatch[1].m_vecNormal +
            uvw.z * TrianglePatch[2].m_vecNormal);
 
        // Find local space point
        float3 p = uvw.x * TrianglePatch[0].m_vecWorldPosition.xyz + uvw.y * TrianglePatch[1].m_vecWorldPosition.xyz + uvw.z * TrianglePatch[2].m_vecWorldPosition.xyz;
        // Find projected vectors
        float3 c0 = project_normal(p, TrianglePatch[0].m_vecWorldPosition.xyz, TrianglePatch[0].m_vecNormal) * uvw.x;
        float3 c1 = project_normal(p, TrianglePatch[1].m_vecWorldPosition.xyz, TrianglePatch[1].m_vecNormal) * uvw.y;
        float3 c2 = project_normal(p, TrianglePatch[2].m_vecWorldPosition.xyz, TrianglePatch[2].m_vecNormal) * uvw.z;
 
        // Interpolate
        output.m_vecWorldPosition.xyz = c0 + c1 + c2;
        output.m_vecWorldPosition.w = uvw.x * TrianglePatch[0].m_vecWorldPosition.w +
            uvw.y * TrianglePatch[1].m_vecWorldPosition.w +
            uvw.z * TrianglePatch[2].m_vecWorldPosition.w;
    }
 
    output.m_vecTextureCoordinate = uvw.x * TrianglePatch[0].m_vecTextureCoordinate +
        uvw.y * TrianglePatch[1].m_vecTextureCoordinate +
        uvw.z * TrianglePatch[2].m_vecTextureCoordinate;
 
    output.m_clipRateAndEdgeColor = uvw.x * TrianglePatch[0].m_clipRateAndEdgeColor +
        uvw.y * TrianglePatch[1].m_clipRateAndEdgeColor +
        uvw.z * TrianglePatch[2].m_clipRateAndEdgeColor;
 
    output.vecTextureIndex = uvw.x * TrianglePatch[0].vecTextureIndex +
        uvw.y * TrianglePatch[1].vecTextureIndex +
        uvw.z * TrianglePatch[2].vecTextureIndex;
 
    output.m_vecStatus = uvw.x * TrianglePatch[0].m_vecStatus +
        uvw.y * TrianglePatch[1].m_vecStatus +
        uvw.z * TrianglePatch[2].m_vecStatus;
 
    output.m_vecColor = uvw.x * TrianglePatch[0].m_vecColor +
        uvw.y * TrianglePatch[1].m_vecColor +
        uvw.z * TrianglePatch[2].m_vecColor;
 
    // Calculate MIP level to fetch normal from
    // float fHeightMapMIPLevel = clamp( ( distance( vRelWorldPos.xyz, vecViewPosition ) - 100.0f ) / 100.0f, 0.0f, 3.0f);
 
    // Sample normal and height map
    float4 vecTexcoord = float4(0.0, 0.0, 0.0, 0.0);
    vecTexcoord.xy = output.m_vecTextureCoordinate.xy;
    vecTexcoord.w = 0; //fHeightMapMIPLevel;
    float parallaxHeight = PAGetTexelLod(texParallax, samParallax, vecTexcoord).x;
 
    // Displace vertex along normal
    float3 flatWorldPos = output.m_vecWorldPosition.xyz;
    output.m_vecWorldPosition.xyz += output.m_vecNormal.xyz * (parallaxHeight * 2.0f - 1.0f) * tessellation_height;
 
    // Transform world position with viewprojection matrix
    output.m_vecPosition = half4(output.m_vecWorldPosition.xyz - vecViewPosition, 1.0);
    output.m_vecPosition = mul(output.m_vecPosition, matViewProj);
 
    // find nearest patch point for recalculate normal.
    float3 vEdge, vRight;
    [branch]
    if (uvw.x == 1.0 || uvw.y == 1.0 || uvw.z == 1.0)
    {
        float3 vCenter = (TrianglePatch[0].m_vecWorldPosition + TrianglePatch[1].m_vecWorldPosition + TrianglePatch[2].m_vecWorldPosition) * 0.33333f;
        vEdge = vCenter - flatWorldPos;
    }
    else if (uvw.x > uvw.y && uvw.x > uvw.z)
    {
        vEdge = flatWorldPos - TrianglePatch[0].m_vecWorldPosition;
    }
    else if (uvw.y > uvw.z)
    {
        vEdge = flatWorldPos - TrianglePatch[1].m_vecWorldPosition;
    }
    else
    {
        vEdge = flatWorldPos - TrianglePatch[2].m_vecWorldPosition;
    }
    vEdge = normalize(vEdge);
    vRight = cross(vEdge, output.m_vecNormal.xyz);
    vEdge = cross(output.m_vecNormal.xyz, vRight);
 
    // recalculate normal
    {
        float2 offset = float2(0.0, 0.0);
        offset.x = dot(output.m_vecTangentU.xyz, vEdge) * texParallaxInvSize.x;
        offset.y = dot(output.m_vecTangentV.xyz, vEdge) * texParallaxInvSize.y;
        float parallaxHeight1 = PAGetTexelLod(texParallax, samParallax, float4(vecTexcoord.xy + offset, 0.0, vecTexcoord.w)).x;
 
        offset.x = dot(output.m_vecTangentU.xyz, vRight) * texParallaxInvSize.x;
        offset.y = dot(output.m_vecTangentV.xyz, vRight) * texParallaxInvSize.y;
        float parallaxHeight2 = PAGetTexelLod(texParallax, samParallax, float4(vecTexcoord.xy + offset, 0.0, vecTexcoord.w)).x;
 
        vEdge += output.m_vecNormal.xyz * (parallaxHeight1 - parallaxHeight) * tessellation_height;
        vRight += output.m_vecNormal.xyz * (parallaxHeight2 - parallaxHeight) * tessellation_height;
        output.m_vecNormal.xyz = cross(normalize(vRight), normalize(vEdge));
    }
 
    return output;
}