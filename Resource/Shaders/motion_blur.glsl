

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
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;
    vec2 velocity = texture2D(texture_velocity, tex_coord).xy * motion_blur_scale;

    float weights = 0.0;

    for( int i = 0; i < 7; i++ )
	{
	    vec2 uv = vec2(tex_coord.x + gaussFilter[i].x * velocity.x, tex_coord.y + gaussFilter[i].x * velocity.y);
		fs_output += texture2D(texture_diffuse, uv) * gaussFilter[i].yyyy;
		weights += gaussFilter[i].y;
	}

	fs_output /= weights;
	fs_output.w = 1.0;
}
#endif // FRAGMENT_SHADER