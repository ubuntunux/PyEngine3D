#version 430 core

#include "screen_space_raycast.glsl"
#include "PCFKernels.glsl"
#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_normal;
uniform sampler2D texture_velocity;
uniform sampler2D texture_depth;


//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
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
    vec4 relative_pos = INV_VIEW_ORIGIN * INV_PERSPECTIVE * ndc_coord;
    relative_pos.xyz /= relative_pos.w;

    vec3 V = normalize(-relative_pos.xyz);
    vec3 N = normalize(texture(texture_normal, vs_output.tex_coord.xy).xyz * 2.0 - 1.0);

    float Roughness = 0.0;
    float RoughnessFade = 1.0;

    const int NumSteps = 8;
    const int NumRays = 4;
    //const int NumSteps = 12;
    //const int NumRays = 12;

    vec2 HitSampleUV = vec2(-1.0, -1.0);

    for (int i = 0; i < NumRays; i++)
    {
        float StepOffset = rand(tex_coord + PoissonSamples[i]) - 0.5;

        vec2 E = Hammersley(i, NumRays, uvec2(PoissonSamples[i]) * uvec2(97, 71));
        vec3 H = TangentToWorld(ImportanceSampleBlinn(E, Roughness).xyz, N);
        vec3 R = 2 * dot(V, H) * H - V;

        vec4 HitUVzTime = RayCast(
            texture_depth,
            VIEW_ORIGIN,
            PERSPECTIVE,
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
            HitSampleUV = HitUVzTime.xy - textureLod(texture_velocity, HitUVzTime.xy, 0.0).xy;
            vec4 SampleColor = SampleScreenColor(texture_diffuse, HitSampleUV);
            SampleColor.rgb /= 1 + Luminance(SampleColor.rgb);
            fs_output += SampleColor;
        }
    }

    fs_output /= NumRays;
    fs_output.rgb /= 1 - Luminance(fs_output.rgb);

    fs_output.w *= RoughnessFade;
}

#endif // FRAGMENT_SHADER