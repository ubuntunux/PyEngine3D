#include "utility.glsl"
#include "PCFKernels.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

const int kernel_size = 32;
uniform vec3 kernel[kernel_size];

uniform float texture_lod;
uniform vec2 texture_size;
uniform vec2 radius_min_max;

uniform sampler2D texture_noise;
uniform sampler2D texture_normal;
uniform sampler2D texture_linear_depth;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;
    vec2 texel_size = 1.0 / texture_size;

    float linear_depth = texture2DLod(texture_linear_depth, tex_coord, texture_lod).x;

    /*if(linear_depth >= NEAR_FAR.y)
    {
        fs_output = vec4(1.0);
        return;
    }*/

    vec4 relative_pos = linear_depth_to_relative_world(tex_coord, linear_depth);
    vec3 normal = texture2D(texture_normal, tex_coord).xyz * 2.0 - 1.0;
    vec2 noise_size = textureSize(texture_noise, 0);

    vec3 randomVec = texture2D(texture_noise, tex_coord * texture_size / noise_size).xyz;

    vec3 tangent   = normalize(randomVec - normal * dot(randomVec, normal));
    vec3 bitangent = cross(normal, tangent);
    mat3 tbn = mat3(tangent, normal, bitangent);

    float occlusion = 0.0;
    int sample_count = min(16, kernel_size);
    for (int i = 0; i < sample_count; ++i)
    {
        vec3 pos = (tbn * kernel[i]) * radius_min_max.y + relative_pos.xyz;

        // project sample position:
        vec4 offset = vec4(pos, 1.0);
        offset = PROJECTION * VIEW_ORIGIN * offset;
        offset.xy /= offset.w;
        offset.xy = offset.xy * 0.5 + 0.5;

        if(offset.x < 0.0 || offset.x > 1.0 || offset.y < 0.0 || offset.y > 1.0)
        {
            continue;
        }

        float sampleDepth = texture2DLod(texture_linear_depth, offset.xy, texture_lod).x;

        if(offset.w < sampleDepth) continue;

        sampleDepth = linear_depth - sampleDepth;
        if(radius_min_max.x <= sampleDepth && sampleDepth <= radius_min_max.y)
        {
            float weight = clamp(1.0 - (sampleDepth - radius_min_max.x) / (radius_min_max.y - radius_min_max.x), 0.0, 1.0);
            occlusion += pow(weight, 3.0);
        }


    }

    occlusion = clamp(1.0 - occlusion / float(sample_count), 0.0, 1.0);
    occlusion *= occlusion;
    fs_output.xyz = vec3(occlusion);
    fs_output.w = 1.0;
}
#endif // FRAGMENT_SHADER