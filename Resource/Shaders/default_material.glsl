//----------- MATERIAL_COMPONENTS ------------//

#define TRANSPARENT_MATERIAL 0

#ifdef MATERIAL_COMPONENTS
    uniform float brightness;
    uniform float reflectance;
    uniform float roughness;
    uniform float metalicness;
    uniform float normal_intensity;
    uniform vec2 uv_tiling;
    uniform vec4 emissive_color;
    uniform vec4 diffuse_color;
    uniform sampler2D texture_diffuse;
    uniform sampler2D texture_material;
    uniform sampler2D texture_normal;
#if TRANSPARENT_MATERIAL == 1
    uniform float opacity;
#endif
#endif

vec4 get_emissive_color()
{
    return emissive_color;
}

vec4 get_base_color(vec2 tex_coord)
{
    vec4 color = texture2D(texture_diffuse, tex_coord);
    // gamma correction
    color.xyz = pow(color.xyz, vec3(2.2));
    color.xyz = color.xyz * brightness * diffuse_color.xyz;
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

vec3 get_normal(vec2 tex_coord)
{
    // Y-Up
    vec3 normal = texture2D(texture_normal, tex_coord).xzy * 2.0 - 1.0;
    normal.xz *= normal_intensity;
    return normalize(normal);
}

float get_ior()
{
    return 1.0;
}

float get_roughness()
{
    return clamp(roughness, 0.05, 1.0);
}

float get_metalicness()
{
    return metalicness;
}

vec3 get_world_offset()
{
    return vec3(1.0, 1.0, 1.0);
}
