#include "scene_constants.glsl"
#include "quad.glsl"

float rand(vec2 uv, float scale)
{
    // This is tiling part, adjusts with the scale...
    uv = mod(uv, scale);
	return fract(sin(dot(uv, vec2(12.9898,78.233))) * 43758.5453123);
}

float noise(vec2 uv, float scale){
    uv *= scale;
	vec2 ij = floor(uv);
	float a = rand((ij + vec2(0.0, 0.0)), scale);
	float b = rand((ij + vec2(1.0, 0.0)), scale);
	float c = rand((ij + vec2(0.0, 1.0)), scale);
	float d = rand((ij + vec2(1.0, 1.0)), scale);

	vec2 xy = fract(uv);
	xy = 0.5 * (1.0 - cos(PI * xy));
	//xy = xy * xy * (3.0 - 2.0 * xy);
	float x1 = mix(a, b, xy.x);
	float x2 = mix(c, d, xy.x);
	return mix(x1, x2, xy.y);
}

float perlinNoise(vec2 p, float scale){
	float persistance = 0.7;
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
    vec2 st = vs_output.tex_coord;
    const int scale = 5;
    float n = perlinNoise(st, float(scale));
    fs_output = vec4(vec3(n), 1.0);
}
#endif