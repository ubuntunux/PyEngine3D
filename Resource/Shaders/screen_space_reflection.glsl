#include "screen_space_raycast.glsl"
#include "PCFKernels.glsl"
#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_random;
uniform sampler2D texture_scene;
uniform sampler2D texture_normal;
uniform sampler2D texture_material;
uniform sampler2D texture_velocity;
uniform sampler2D texture_depth;

uint ReverseBits32( uint bits )
{
    bits = ( bits << 16) | ( bits >> 16);
	bits = ( (bits & 0x00ff00ff) << 8 ) | ( (bits & 0xff00ff00) >> 8 );
	bits = ( (bits & 0x0f0f0f0f) << 4 ) | ( (bits & 0xf0f0f0f0) >> 4 );
	bits = ( (bits & 0x33333333) << 2 ) | ( (bits & 0xcccccccc) >> 2 );
	bits = ( (bits & 0x55555555) << 1 ) | ( (bits & 0xaaaaaaaa) >> 1 );
	return bits;
}

vec2 Hammersley( uint Index, uint NumSamples, uvec2 Random )
{
	float E1 = fract( float(Index) / NumSamples + float( Random.x & 0xffff ) / (1<<16) );
	float E2 = float( ReverseBits32(Index) ^ Random.y ) * 2.3283064365386963e-10;
	return vec2( E1, E2 );
}

float ClampedPow(float X, float Y)
{
    return pow(max(abs(X), 0.000001f), Y);
}

vec4 ImportanceSampleBlinn(vec2 E, float Roughness)
{
    float PI = 3.14159265f;
    float m = Roughness * Roughness;
    float n = 2 / (m*m) - 2;

    float Phi = 2 * PI * E.x;
    float CosTheta = ClampedPow(E.y, 1 / (n + 1));
    float SinTheta = sqrt(1 - CosTheta * CosTheta);

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
    vec3 UpVector = abs(TangentY.y) < 0.999 ? vec3(0, 1, 0) : vec3(0, 0, 1);
    vec3 TangentZ = normalize(cross(UpVector, TangentY));
    vec3 TangentX = cross(TangentY, TangentZ);
    return mat3(TangentX, TangentY, TangentZ);
}

vec3 TangentToWorld(vec3 vector, vec3 TangentY)
{
    return GetTangentBasis(TangentY) * vector;
}

vec4 SampleScreenColor(sampler2D texPrevSceneColor, vec2 UV, float lod)
{
    vec4 OutColor;
    OutColor.xyz = texture2DLod(texPrevSceneColor, UV, lod).xyz;
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

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    fs_output = vec4(0.0);

    vec2 tex_coord = vs_output.tex_coord.xy;
    float linear_depth = texture2D(texture_depth, tex_coord).x;
    float depth = linear_depth_to_depth(linear_depth);

    if(depth >= 1.0)
    {
        return;
    }

    ivec2 PixelPos = ivec2(gl_FragCoord.xy);

    vec4 ndc_coord = vec4(vs_output.tex_coord.xy * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 relative_pos = INV_VIEW_ORIGIN * INV_PROJECTION * ndc_coord;
    relative_pos.xyz /= relative_pos.w;

    vec3 V = normalize(-relative_pos.xyz);
    vec3 N = normalize(texture2D(texture_normal, vs_output.tex_coord.xy).xyz * 2.0 - 1.0);
    float NdotV = dot(V, N);

    if(0.9 < NdotV)
    {
        return;
    }

    float fresnel = pow(1.0 - clamp(NdotV, 0.0, 1.0), 4.0);
    float Roughness = texture2D(texture_material, vs_output.tex_coord.xy).x;
    Roughness = mix(Roughness, Roughness * Roughness, fresnel);
    float sqrtRoughness = sqrt(Roughness);

    const int NumSteps = 16;
    const int NumRays = 8;

    vec2 HitSampleUV = vec2(-1.0, -1.0);
    float hit_count = 0.0;
    vec2 random_texture_size = textureSize(texture_random, 0);

    for (int i = 0; i < NumRays; i++)
    {
        vec2 poisson = PoissonSamples[int(JITTER_FRAME + i * PoissonSampleCount / NumRays) % PoissonSampleCount];
        vec2 random = texture2D(texture_random, tex_coord + poisson).xy;
        float StepOffset = 0.5 - rand(tex_coord + random);

        vec2 E = Hammersley(i, NumRays, uvec2(random * 117));
        vec3 H = TangentToWorld(ImportanceSampleBlinn( random, sqrtRoughness * 0.5 ).xyz, N);
        vec3 R = reflect(-V, H);

        vec4 HitUVzTime = RayCast(
            texture_depth,
            VIEW_ORIGIN,
            PROJECTION,
            relative_pos.xyz,
            R,
            Roughness,
            0.001,
            linear_depth * 0.01,
            NumSteps,
            StepOffset
        );

        // if there was a hit
        if (HitUVzTime.w < 1)
        {
            HitSampleUV = HitUVzTime.xy - texture2D(texture_velocity, HitUVzTime.xy).xy;
            vec4 SampleColor = SampleScreenColor(texture_scene, HitSampleUV, sqrtRoughness * 6.0);
            SampleColor.rgb /= 1 + get_luminance(SampleColor.rgb);
            fs_output += SampleColor;
            hit_count += 1.0;
        }
    }

    if(0.0 < hit_count)
    {
        fs_output.rgb /= hit_count;
        fs_output.rgb /= 1.0 - get_luminance(fs_output.rgb);
        fs_output.a /= NumRays;
    }
}

#endif // FRAGMENT_SHADER