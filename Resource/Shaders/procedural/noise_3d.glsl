#include "scene_constants.glsl"
#include "quad.glsl"

uniform float depth;
uniform float noise_persistance;
uniform int noise_scale;
uniform float noise_seed;


float rand(vec3 uvw, float scale)
{
    // This is tiling part, adjusts with the scale...
    uvw = mod(uvw + vec3(fract(noise_seed)), scale);
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
layout (location = 0) out vec4 fs_output;

void main() {
    vec3 st = vec3(vs_output.tex_coord, depth);
    float n = perlinNoise( st, float(noise_scale), noise_persistance);
    fs_output = vec4(n);
}
#endif