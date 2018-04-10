#include "blending.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform float depth;
uniform float random_seed;
uniform int sphere_count;
uniform float sphere_scale;
uniform sampler2D texture_random;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out float fs_output;


void main() {
    vec3 uvw = vec3(vs_output.tex_coord, depth);
    float density_max = 1.0;

    vec2 texture_size = textureSize(texture_random, 0);
    float texel_count = texture_size.x * texture_size.y;

    vec4 sphere;

    for(int i=0; i<sphere_count; ++i)
    {
        float texture_index = mod(float(i) + random_seed * texel_count, texel_count);
        vec2 texture_uv;
        texture_uv.x = texture_index / texture_size.x;
        texture_uv.y = floor(texture_uv.x);
        texture_uv.x = texture_uv.x - texture_uv.y;
        texture_uv.y /= texture_size.y;

        sphere = texture(texture_random, texture_uv);
        sphere.w = mix(0.7, 1.0, sphere.w) * sphere_scale * 0.3;

        // find nearest sphere for outside sphere of uvw.
        vec3 diff = abs(sphere.xyz - uvw);
        diff = min(diff, abs(vec3(1.0) - diff));

        density_max = min(density_max, length(diff) / sphere.w);
    }

    float density_max2 = 1.0;

    for(int i=0; i<sphere_count / 10; ++i)
    {
        float texture_index = mod(float(i) + random_seed * texel_count, texel_count);
        vec2 texture_uv;
        texture_uv.x = texture_index / texture_size.x;
        texture_uv.y = floor(texture_uv.x);
        texture_uv.x = texture_uv.x - texture_uv.y;
        texture_uv.y /= texture_size.y;

        sphere = texture(texture_random, texture_uv);
        sphere.w = mix(0.7, 1.0, sphere.w);

        // find nearest sphere for outside sphere of uvw.
        vec3 diff = abs(sphere.xyz - uvw);
        diff = min(diff, abs(vec3(1.0) - diff));

        density_max2 = min(density_max2, length(diff) / sphere.w);
    }

    fs_output = (1.0 - density_max) * pow(1.0 - density_max2, 2.0);
}
#endif