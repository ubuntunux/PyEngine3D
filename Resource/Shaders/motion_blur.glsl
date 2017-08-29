#version 430 core

#include "quad.glsl"

uniform float motionblur_scale;
uniform sampler2D texture_diffuse;
uniform sampler2D texture_velocity;

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    vec2 texcoord = vs_output.texcoord.xy;
    vec2 velocity = texture(texture_velocity, texcoord).xy * motionblur_scale;

    vec4 color = texture(texture_diffuse, texcoord);

    color += texture(texture_diffuse, clamp(texcoord + velocity, 0.0, 1.0));
    color += texture(texture_diffuse, clamp(texcoord - velocity, 0.0, 1.0));
    color += texture(texture_diffuse, clamp(texcoord + velocity * 0.75, 0.0, 1.0));
    color += texture(texture_diffuse, clamp(texcoord - velocity * 0.75, 0.0, 1.0));
    color += texture(texture_diffuse, clamp(texcoord + velocity * 0.5, 0.0, 1.0));
    color += texture(texture_diffuse, clamp(texcoord - velocity * 0.5, 0.0, 1.0));
    color += texture(texture_diffuse, clamp(texcoord + velocity * 0.25, 0.0, 1.0));
    color += texture(texture_diffuse, clamp(texcoord - velocity * 0.25, 0.0, 1.0));
    color += texture(texture_diffuse, clamp(texcoord + velocity * 0.125, 0.0, 1.0));
    color += texture(texture_diffuse, clamp(texcoord - velocity * 0.125, 0.0, 1.0));

    fs_output.xyz = color.xyz / vec3(11.0);
    fs_output.a = 1.0;
}
#endif // FRAGMENT_SHADER