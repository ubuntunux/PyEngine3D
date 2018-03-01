#include "scene_constants.glsl"
#include "quad.glsl"

float rand(vec2 c){
	return fract(sin(dot(c, vec2(12.9898,78.233))) * 43758.5453123);
}

float noise(vec2 p, float freq){
    float unit = 1.0 / freq;
	vec2 ij = floor(p / unit);
	vec2 xy = mod(p, unit) / unit;
	xy = 0.5 * (1.0 - cos(PI * xy));
	float a = rand((ij + vec2(0.0, 0.0)));
	float b = rand((ij + vec2(1.0, 0.0)));
	float c = rand((ij + vec2(0.0, 1.0)));
	float d = rand((ij + vec2(1.0, 1.0)));

	float x1 = mix(a, b, xy.x);
	float x2 = mix(c, d, xy.x);
	return mix(x1, x2, xy.y);
}

float perlinNoise(vec2 p){
	float persistance = 0.7;
	float n = 0.0;
	float weights = 0.0;
	float freq = 4.0;
	float amp = 1.0;
	for (int i = 0; i<50; i++)
	{
		n += amp * noise(p, freq);
		weights += amp;
		amp *= persistance;
		freq *= 2.0;
	}
	return n / weights;
}

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 st = vs_output.tex_coord;
    float n = perlinNoise(st * 2.0);
    fs_output = vec4(vec3(n), 1.0);
}
#endif