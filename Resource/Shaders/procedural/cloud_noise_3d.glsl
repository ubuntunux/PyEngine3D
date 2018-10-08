#include "blending.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform float depth;
uniform float random_seed;
uniform int sphere_count;
uniform float sphere_scale;
uniform sampler2D texture_random;

uniform float noise_persistance;
uniform int noise_scale;


float rand(vec3 uvw, float scale)
{
    // This is tiling part, adjusts with the scale...
    uvw = mod(uvw + vec3(random_seed), scale);
	return fract(sin(dot(uvw, vec3(12.9898, 78.233, 45.164))) * 43758.5453123);
}


// This one has non-ideal tiling properties that I'm still tuning
float noise(vec3 x, float scale)
{
	const vec3 step = vec3(110, 241, 171);

	x *= scale;
	vec3 i = floor(x);
	vec3 f = fract(x);

	vec3 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix( rand(i + vec3(0, 0, 0), scale), rand(i + vec3(1, 0, 0), scale), u.x),
                   mix( rand(i + vec3(0, 1, 0), scale), rand(i + vec3(1, 1, 0), scale), u.x), u.y),
               mix(mix( rand(i + vec3(0, 0, 1), scale), rand(i + vec3(1, 0, 1), scale), u.x),
                   mix( rand(i + vec3(0, 1, 1), scale), rand(i + vec3(1, 1, 1), scale), u.x), u.y), u.z);
}

float perlinNoise(vec3 p, float scale, float persistance)
{
	float n = 0.0;
	float weights = 0.0;
	float amp = 1.0;
	for (int i = 0; i<50; i++)
	{
		n += amp * noise(p, scale);
		weights += amp;
		amp *= persistance;
		scale *= 2.0;
	}
	return n / weights;
}

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out float fs_output;


void main() {
    vec3 uvw = vec3(vs_output.tex_coord, depth);
    vec2 texture_size = textureSize(texture_random, 0);
    float texel_count = texture_size.x * texture_size.y;

    float final_density = 0.0;
    float acc_scale = sphere_scale;
    int acc_count = sphere_count;
    vec4 sphere;

    const int layer_count = 4;
    float total_weight = 0.0;
    float weight = 1.0;
    for(int l=0; l<layer_count; ++l)
    {
        float density = 1.0;
        for(int i=0; i<acc_count; ++i)
        {
            float texture_index = mod(float(i) + random_seed * texel_count, texel_count);
            vec2 texture_uv;
            texture_uv.x = texture_index / texture_size.x;
            texture_uv.y = floor(texture_uv.x);
            texture_uv.x = texture_uv.x - texture_uv.y;
            texture_uv.y /= texture_size.y;

            sphere = texture2D(texture_random, texture_uv);
            sphere.w = mix(0.7, 1.0, sphere.w) * acc_scale;

            // find nearest sphere for outside sphere of uvw.
            vec3 diff = abs(sphere.xyz - uvw);
            diff = min(diff, abs(vec3(1.0) - diff));

            density = min(density, length(diff) / sphere.w);
        }
        final_density += (1.0 - density) * weight;
        total_weight += weight;
        weight *= 0.6;
        acc_count = int(sqrt(acc_count));
        acc_scale += sphere_scale;
    }

    float noise = perlinNoise(uvw, float(noise_scale), noise_persistance);
    noise = Contrast(noise, 2.0);

    final_density /= total_weight;
    final_density = mix(noise, 1.0, final_density);

    // final_density = Remap(noise, final_density, 1.0, 0.0, 1.0);
    fs_output = final_density;
}
#endif