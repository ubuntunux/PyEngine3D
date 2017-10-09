#version 430 core

#include "quad.glsl"

uniform float motion_blur_scale;
uniform sampler2D texture_diffuse;
uniform sampler2D texture_velocity;

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
    vec2 velocity = texture(texture_velocity, texcoord).xy * motion_blur_scale;

    float weights = 0.0;

    for( int i = 0; i < 7; i++ )
	{
	    vec2 uv = vec2(texcoord.x + gaussFilter[i].x * velocity.x, texcoord.y + gaussFilter[i].x * velocity.y);
		fs_output += texture(texture_diffuse, uv) * gaussFilter[i].yyyy;
		weights += gaussFilter[i].y;
	}

	fs_output /= weights;
	fs_output.w = 1.0;
}
#endif // FRAGMENT_SHADER