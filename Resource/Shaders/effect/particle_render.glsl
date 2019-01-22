#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = INSTANCE_ID_LOCATION) flat in uint instanceID;

layout (location = 0) out vec4 ps_output;

void main()
{
    vec4 diffuse = texture2D(texture_diffuse, vs_output.uv);

    if(vs_output.uv.x != vs_output.next_uv.x || vs_output.uv.y != vs_output.next_uv.y)
    {
        diffuse = mix(diffuse, texture2D(texture_diffuse, vs_output.next_uv), vs_output.sequence_ratio);
    }

    ps_output.xyz = pow(diffuse.xyz, vec3(2.2)) * PARTICLE_COLOR.xyz;
    ps_output.w = diffuse.w * vs_output.opacity;

    if(ADDITIVE == PARTICLE_BLEND_MODE || SUBTRACT == PARTICLE_BLEND_MODE)
    {
        ps_output.xyz *= ps_output.w;
        ps_output.w = 0.0;
    }
    else if(MULTIPLY == PARTICLE_BLEND_MODE)
    {
        ps_output.xyz = mix(vec3(1.0), ps_output.xyz, vec3(ps_output.w));
        ps_output.w = 1.0;
    }
}
#endif