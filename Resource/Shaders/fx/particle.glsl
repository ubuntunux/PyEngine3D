#include "scene_constants.glsl"
#include "utility.glsl"
#include "fx/particle_vs.glsl"


#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 ps_output;

void main()
{
    vec4 diffuse = texture2D(texture_diffuse, vs_output.uv);

    if(vs_output.uv.x != vs_output.next_uv.x || vs_output.uv.y != vs_output.next_uv.y)
    {
        diffuse = mix(diffuse, texture2D(texture_diffuse, vs_output.next_uv), vs_output.sequence_ratio);
    }

    ps_output.xyz = pow(diffuse.xyz, vec3(2.2)) * EMITTER_COLOR.xyz;
    ps_output.w = diffuse.w * vs_output.opacity;

    if(ADDITIVE == EMITTER_BLEND_MODE || SUBTRACT == EMITTER_BLEND_MODE)
    {
        ps_output.xyz *= ps_output.w;
    }
    else if(MULTIPLY == EMITTER_BLEND_MODE)
    {
        ps_output.xyz = mix(vec3(1.0), ps_output.xyz, vec3(ps_output.w));
    }
}
#endif