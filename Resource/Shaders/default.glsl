#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "default_material.glsl"
#include "default_vs.glsl"

uniform bool is_render_gbuffer;

uniform sampler2D texture_depth;
uniform sampler2D texture_shadow;
uniform sampler2D texture_ssao;
uniform sampler2D texture_scene_reflect;
uniform samplerCube texture_probe;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;

layout (location = 0) out vec4 fs_diffuse;
layout (location = 1) out vec4 fs_material;
layout (location = 2) out vec4 fs_normal;
#if 1 == SKELETAL
layout (location = 3) out vec2 fs_velocity;
#endif

void main()
{
    vec2 screen_tex_coord = vs_output.projection_pos.xy / vs_output.projection_pos.w * 0.5 + 0.5;
    float depth = texture2D(texture_depth, screen_tex_coord).x;
    vec4 base_color = get_base_color(vs_output.tex_coord.xy);

#if TRANSPARENT_MATERIAL == 1
    base_color.a *= opacity;
#else
    if(base_color.a < 0.333)
    {
        discard;
    }
#endif

    vec4 emissive_color = get_emissive_color();
    vec4 material_factors = texture2D(texture_material, vs_output.tex_coord.xy);
    float ao_factor = material_factors.x;
    float roughness_factor = material_factors.y * get_roughness();
    float metallic_factor = material_factors.z * get_metalicness();

    base_color.xyz *= ao_factor;

    vec3 N = get_normal(vs_output.tex_coord.xy);

    // Note : Normalization is very important because tangent_to_world may have been scaled..
    N = normalize((vs_output.tangent_to_world * vec4(N, 0.0)).xyz);
    vec3 V = normalize(CAMERA_POSITION.xyz - vs_output.world_position);
    vec3 L = normalize(LIGHT_DIRECTION.xyz);

    // Render GBuffer
    if(is_render_gbuffer)
    {
        fs_diffuse.xyz = base_color.xyz + base_color.xyz * emissive_color.xyz * emissive_color.w * 0.5;
        // emissive
        fs_diffuse.w = saturate(get_luminance(emissive_color.xyz * 0.5) * emissive_color.w * 0.1);
        fs_material = vec4(roughness_factor, metalicness, reflectance, 0.0);
        fs_normal = vec4(N * 0.5 + 0.5, 0.0);
#if 1 == SKELETAL
        fs_velocity = (vs_output.projection_pos.xy / vs_output.projection_pos.w) - (vs_output.prev_projection_pos.xy / vs_output.prev_projection_pos.w);
        // NDC coord -> Screen Coord
        fs_velocity *= 0.5;
        fs_velocity.xy -= JITTER_DELTA;
#endif
    }
    else
    {
        // Render Forward
        fs_diffuse = surface_shading(
                        base_color,
                        base_color.xyz * emissive_color.xyz * emissive_color.w,
                        metalicness,
                        metallic_factor,
                        reflectance,
                        texture2D(texture_ssao, screen_tex_coord).x,
                        texture2D(texture_scene_reflect, screen_tex_coord),
                        texture_probe,
                        texture_shadow,
                        screen_tex_coord,
                        vs_output.world_position,
                        LIGHT_COLOR.xyz,
                        N,
                        V,
                        L,
                        depth);
    }
}
#endif