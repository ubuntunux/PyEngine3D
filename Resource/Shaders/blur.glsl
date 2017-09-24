#version 430 core

#include "quad.glsl"

uniform float lod;
uniform vec2 blur_scale;
uniform sampler2D texture_diffuse;

const vec2 gaussFilter[7] =
{
	vec2(-3.0,	0.015625),
	vec2(-2.0,	0.09375),
	vec2(-1.0,	0.234375),
	vec2(0.0,	0.3125),
	vec2(1.0,	0.234375),
	vec2(2.0,	0.09375),
	vec2(3.0,	0.015625)
};

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;
void main() {
    vec2 texcoord = vs_output.texcoord.xy;
    vec2 scale = blur_scale / textureSize(texture_diffuse, 0);

    fs_output = vec4(0.0, 0.0, 0.0, 1.0);

    for( int i = 0; i < 7; i++ )
	{
	    vec2 uv = vec2(texcoord.x + gaussFilter[i].x * scale.x, texcoord.y + gaussFilter[i].x * scale.y);
		fs_output += texture(texture_diffuse, uv) * gaussFilter[i].yyyy;
	}
}
#endif // FRAGMENT_SHADER