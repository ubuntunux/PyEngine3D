//----------- MATERIAL_COMPONENTS ------------//

#ifdef MATERIAL_COMPONENTS
    uniform int enable_blend;
    uniform float brightness;
    uniform vec4 emissive_color;
    uniform vec4 diffuse_color;
    uniform sampler2D texture_diffuse;
    uniform sampler2D texture_normal;
#endif

vec4 get_emissive_color()
{
    return emissive_color;
}

vec4 get_base_color(vec2 texcoord)
{
    vec4 color = texture(texture_diffuse, texcoord);
    color.xyz = color.xyz * brightness * diffuse_color.xyz * diffuse_color.a;
    return color;
}

float get_reflection()
{
    return 1.0;
}

vec3 get_edge_tint_color()
{
    return vec3(1.0, 1.0, 1.0);
}

vec3 get_sss_color()
{
    return vec3(1.0, 1.0, 1.0);
}

float get_sss_scale()
{
    return 1.0;
}

vec3 get_normal(vec2 texcoord)
{
    // Y-Up
    vec3 normal = texture(texture_normal, texcoord).xzy * 0.5 - 0.5;
    return normalize(normal);
}

float get_ior()
{
    return 1.0;
}

float get_roughness()
{
    return 1.0;
}

float get_metalicness()
{
    return 1.0;
}

vec3 get_world_offset()
{
    return vec3(1.0, 1.0, 1.0);
}
