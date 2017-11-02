//----------- MATERIAL_COMPONENTS ------------//

#ifdef MATERIAL_COMPONENTS
    uniform int enable_blend;
    uniform float brightness;
    uniform float roughness;
    uniform vec4 emissive_color;
    uniform vec4 diffuse_color;
    uniform sampler2D texture_diffuse;
    uniform sampler2D texture_surface;
    uniform sampler2D texture_normal;
    uniform samplerCube texture_cube;
#endif

vec4 get_emissive_color()
{
    return emissive_color;
}

vec4 get_base_color(vec2 tex_coord)
{
    vec4 color = texture(texture_diffuse, tex_coord);
    // gamma correction
    color.xyz = pow(color.xyz, vec3(2.2));
    color.xyz = color.xyz * brightness * diffuse_color.xyz * diffuse_color.a;
    return color;
}

float get_reflection()
{
    return 1.0;
}

vec4 get_reflection_color(vec3 reflection_vector)
{
    // Invert Y axis
    reflection_vector.y = 1.0 - reflection_vector.y;

    vec4 reflection_color = texture(texture_cube, reflection_vector);
    reflection_color.xyz = pow(reflection_color.xyz, vec3(2.2));
    return reflection_color;
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

vec3 get_normal(vec2 tex_coord)
{
    // Y-Up
    vec3 normal = texture(texture_normal, tex_coord).xzy * 2.0 - 1.0;
    return normalize(normal);
}

float get_ior()
{
    return 1.0;
}

float get_roughness()
{
    return roughness;
}

float get_metalicness()
{
    return 1.0;
}

vec3 get_world_offset()
{
    return vec3(1.0, 1.0, 1.0);
}
