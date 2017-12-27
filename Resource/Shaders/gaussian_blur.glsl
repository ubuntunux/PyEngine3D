

#include "quad.glsl"

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

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 tex_coord = vs_output.tex_coord.xy;
    vec2 scale = blur_scale / textureSize(texture_diffuse, 0);

    fs_output = vec4(0.0, 0.0, 0.0, 1.0);

    for( int i = 0; i < 7; i++ )
	{
	    vec2 uv = vec2(tex_coord.x + gaussFilter[i].x * scale.x, tex_coord.y + gaussFilter[i].x * scale.y);
		fs_output += texture(texture_diffuse, uv) * gaussFilter[i].yyyy;
	}
}
#endif // GL_FRAGMENT_SHADER