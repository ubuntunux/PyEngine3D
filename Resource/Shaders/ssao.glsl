#version 430 core

#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_normal;
uniform sampler2D texture_depth;
uniform sampler2D texture_linear_depth;

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

const int uSampleKernelSize = 16;

void main() {
    vec2 texcoord = vs_output.texcoord.xy;
    float depth = texture(texture_linear_depth, texcoord).x;
    vec4 clip_coord = vec4(texcoord * 2.0 - 1.0, -1.0, 1.0);
    vec4 view_ray = inv_view_origin * inv_perspective * clip_coord;
    view_ray /= view_ray.w;
    view_ray.xyz = normalize(view_ray.xyz);
    vec3 world_pos = view_ray.xyz * depth;
    vec3 normal = texture(texture_normal, texcoord).xyz;

    vec3 randomVec = normalize(vec3(rand(texcoord.xy), rand(texcoord.xy * texcoord.yx), rand(texcoord.yx)));

    vec3 tangent   = normalize(randomVec - normal * dot(randomVec, normal));
    vec3 bitangent = cross(normal, tangent);
    mat3 tbn = mat3(tangent, bitangent, normal);


    float occlusion = 0.0;
    float uRadius = 0.1;
    for (int i = 0; i < uSampleKernelSize; ++i) {
        // get sample position:
        vec3 pos = tbn * normalize(vec3(rand(texcoord.xy + vec2(uSampleKernelSize * 0.1)), 1.0, rand(texcoord.yx + vec2(uSampleKernelSize * 0.1))));
        pos = pos * uRadius * rand(texcoord.xy + vec2(uSampleKernelSize * 0.3)) + world_pos;

        // project sample position:
        vec4 offset = vec4(pos, 1.0);
        offset = perspective * view_origin * offset;
        offset.xy /= offset.w;
        offset.xy = offset.xy * 0.5 + 0.5;

        // get sample depth:
        float sampleDepth = texture(texture_linear_depth, offset.xy).r;

        // range check & accumulate:
        float rangeCheck = abs(world_pos.z - sampleDepth) < uRadius ? 1.0 : 0.0;
        occlusion += (sampleDepth <= depth ? 1.0 : 0.0);
    }

    occlusion = 1.0 - occlusion / (float(uSampleKernelSize) - 1.0);
    fs_output.xyz = vec3(occlusion);
    fs_output.w = 1.0;

}
#endif // FRAGMENT_SHADER