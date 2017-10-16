#version 430 core

#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform vec2 screen_size;
uniform vec2 radius_min_max;

const int kernel_size = 32;
uniform vec3 kernel[kernel_size];

uniform sampler2D texture_noise;
uniform sampler2D texture_normal;
uniform sampler2D texture_linear_depth;

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    vec2 texcoord = vs_output.texcoord.xy;
    float linear_depth = texture(texture_linear_depth, texcoord).x;

    /*if(linear_depth >= near_far.y)
    {
        fs_output = vec4(1.0);
        return;
    }*/

    vec4 relative_pos = linear_depth_to_relative_world(texcoord, linear_depth);
    vec3 normal = texture(texture_normal, texcoord).xyz * 2.0 - 1.0;
    vec2 noise_size = textureSize(texture_noise, 0);
    vec3 randomVec = texture(texture_noise, texcoord * screen_size / noise_size).xyz;

    vec3 tangent   = normalize(randomVec - normal * dot(randomVec, normal));
    vec3 bitangent = cross(normal, tangent);
    mat3 tbn = mat3(tangent, normal, bitangent);

    float occlusion = 0.0;
    for (int i = 0; i < kernel_size; ++i) {
        // get sample position:
        vec3 pos = tbn * kernel[i];
        pos = pos * radius_min_max.y + relative_pos.xyz;

        // project sample position:
        vec4 offset = vec4(pos, 1.0);
        offset = perspective * view_origin * offset;
        offset.xy /= offset.w;
        offset.xy = offset.xy * 0.5 + 0.5;

        // check out point of screen.
        if(offset.x < 0.0 || offset.x > 1.0 || offset.y < 0.0 || offset.y > 1.0)
        {
            continue;
        }

        // get sample depth:
        float sampleDepth = texture(texture_linear_depth, offset.xy).r;

        // range check & accumulate:
        float delta = linear_depth - sampleDepth;
        if(delta > radius_min_max.x && abs(delta) < radius_min_max.y )
        {
            occlusion += 1.0;
        }
    }

    occlusion = 1.0 - occlusion / (float(kernel_size) - 1.0);
    occlusion *= occlusion;
    fs_output.xyz = vec3(occlusion);
    fs_output.w = 1.0;

}
#endif // FRAGMENT_SHADER