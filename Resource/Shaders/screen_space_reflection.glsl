#include "screen_space_raycast.glsl"
#include "PCFKernels.glsl"
#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_normal;
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
    vec3 UpVector = abs(TangentY.z) < 0.999 ? vec3(0, 1, 0) : vec3(0, 0, 1);
    vec3 TangentX = normalize(cross(UpVector, TangentY));
    vec3 TangentZ = cross(TangentY, TangentX);
    return mat3(TangentX, TangentY, TangentZ);
}

vec3 TangentToWorld(vec3 vector, vec3 TangentY)
{
    return GetTangentBasis(TangentY) * vector;
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

#ifdef GL_FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    fs_output = vec4(0.0);
    vec2 tex_coord = vs_output.tex_coord.xy;
    float depth = texture(texture_depth, tex_coord).x;

    if(depth >= 1.0)
    {
        return;
    }

    ivec2 PixelPos = ivec2(gl_FragCoord.xy);
    float linear_depth = depth_to_linear_depth(depth) * 0.1;

    vec4 ndc_coord = vec4(vs_output.tex_coord.xy * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 relative_pos = INV_VIEW_ORIGIN * INV_PROJECTION * ndc_coord;
    relative_pos.xyz /= relative_pos.w;

    vec3 V = normalize(-relative_pos.xyz);
    vec3 N = normalize(texture(texture_normal, vs_output.tex_coord.xy).xyz * 2.0 - 1.0);


    float Roughness = 0.0;
    float RoughnessFade = 1.0;

    const int NumSteps = 8;
    const int NumRays = 8;
    //const int NumSteps = 12;
    //const int NumRays = 12;

    vec2 HitSampleUV = vec2(-1.0, -1.0);

    for (int i = 0; i < NumRays; i++)
    {
        vec2 poisson =  PoissonSamples[int(JITTER_FRAME + i) % PoissonSampleCount];
        float StepOffset = rand(tex_coord + poisson) - 0.5;

        vec2 E = Hammersley( i, NumRays, uvec2(poisson * 117) );
        vec3 H = TangentToWorld(ImportanceSampleBlinn( PoissonSamples[i * PoissonSampleCount / NumRays], Roughness ).xyz, N);
        vec3 R = reflect(-V, H);

        vec4 HitUVzTime = RayCast(
            texture_depth,
            VIEW_ORIGIN,
            PROJECTION,
            relative_pos.xyz,
            R,
            Roughness,
            0.001,
            linear_depth,
            NumSteps,
            StepOffset
        );

        // if there was a hit
        if (HitUVzTime.w < 1)
        {
            HitSampleUV = HitUVzTime.xy - texture(texture_velocity, HitUVzTime.xy).xy;
            vec4 SampleColor = SampleScreenColor(texture_diffuse, HitSampleUV);
            SampleColor.rgb /= 1 + get_linear_luminance(SampleColor.rgb);
            fs_output += SampleColor;
        }
    }

    fs_output /= NumRays;
    fs_output.rgb /= 1 - get_linear_luminance(fs_output.rgb);

    fs_output.w *= RoughnessFade;
}

#endif // GL_FRAGMENT_SHADER