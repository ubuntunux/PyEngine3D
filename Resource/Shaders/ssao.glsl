#include "utility.glsl"
#include "PCFKernels.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

const int kernel_size = 32;
uniform vec3 kernel[kernel_size];

uniform bool isHalfSize;
uniform vec2 texture_size;
uniform vec2 radius_min_max;

uniform sampler2D texture_noise;
uniform sampler2D texture_normal;
uniform sampler2D texture_linear_depth;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;

    float linear_depth = 0.0;
    if(isHalfSize)
    {
        vec4 depthGather = textureGather(texture_linear_depth, tex_coord, 0);
        linear_depth = (depthGather.x + depthGather.y + depthGather.z + depthGather.w) * 0.25;
    }
    else
    {
        linear_depth = texture(texture_linear_depth, tex_coord).x;
    }

    /*if(linear_depth >= NEAR_FAR.y)
    {
        fs_output = vec4(1.0);
        return;
    }*/

    vec4 relative_pos = linear_depth_to_relative_world(tex_coord, linear_depth);
    vec3 normal = texture(texture_normal, tex_coord).xyz * 2.0 - 1.0;
    vec2 noise_size = textureSize(texture_noise, 0);

    float offset = rand(tex_coord);
    offset = offset * texture_size.x + offset * texture_size.y;
    vec2 poisson =  PoissonSamples[int(JITTER_FRAME + offset) % PoissonSampleCount];
    vec3 randomVec = texture(texture_noise, (tex_coord * texture_size + poisson)/ noise_size).xyz;

    vec3 tangent   = normalize(randomVec - normal * dot(randomVec, normal));
    vec3 bitangent = cross(normal, tangent);
    mat3 tbn = mat3(tangent, normal, bitangent);

    float occlusion = 0.0;
    int sample_count = kernel_size;
    for (int i = 0; i < sample_count; ++i) {
        // get sample position:
        vec3 pos = tbn * kernel[i];
        pos = pos * radius_min_max.y + relative_pos.xyz;

        // project sample position:
        vec4 offset = vec4(pos, 1.0);
        offset = PROJECTION * VIEW_ORIGIN * offset;
        offset.xy /= offset.w;
        offset.xy = offset.xy * 0.5 + 0.5;

        if(offset.x < 0.0 || offset.x > 1.0 || offset.y < 0.0 || offset.y > 1.0)
        {
            continue;
        }

        vec4 sampleDepth = textureGather(texture_linear_depth, offset.xy, 0);

        const float amount = 0.25;
        for(int j=0; j<4; ++j)
        {
            sampleDepth[j] = linear_depth - sampleDepth[j];
            if(sampleDepth[j] > radius_min_max.x && abs(sampleDepth[j]) < radius_min_max.y )
            {
                occlusion += clamp(amount * (0.5 + sampleDepth[j]), 0.0, amount);
                //occlusion += amount;
            }
        }
    }

    occlusion = clamp(1.0 - occlusion / (float(sample_count) - 1.0), 0.0, 1.0);
    occlusion *= occlusion;
    fs_output.xyz = vec3(occlusion);
    fs_output.w = 1.0;
}
#endif // GL_FRAGMENT_SHADER