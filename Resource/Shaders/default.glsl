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

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;

layout (location = 0) out vec4 fs_diffuse;
layout (location = 1) out vec4 fs_material;
layout (location = 2) out vec4 fs_normal;
layout (location = 3) out vec2 fs_velocity;

void main() {
    vec2 screen_tex_coord = vs_output.projection_pos.xy / vs_output.projection_pos.w * 0.5 + 0.5;
    float depth = texture(texture_depth, screen_tex_coord).x;
    vec4 base_color = get_base_color(vs_output.tex_coord.xy);

#if TRANSPARENT_MATERIAL == 1
    base_color.a *= opacity;
#else
    if(base_color.a < 0.333f)
    {
        discard;
    }
#endif

    vec4 emissive_color = get_emissive_color();

    vec3 N = get_normal(vs_output.tex_coord.xy);
    // Note : Normalization is very important because tangent_to_world may have been scaled..
    N = normalize((vs_output.tangent_to_world * vec4(N, 0.0)).xyz);
    vec3 V = normalize(CAMERA_POSITION.xyz - vs_output.world_position);
    vec3 L = normalize(LIGHT_DIRECTION.xyz);

    if(is_render_gbuffer)
    {
        fs_diffuse.xyz = base_color.xyz + emissive_color.xyz * clamp(emissive_color.w, 0.0, 1.0);
        // encoding
        fs_diffuse.w = (get_linear_luminance(emissive_color.xyz) * emissive_color.w) * 0.1;

        fs_material = vec4(get_roughness(), metalicness, reflectance, 0.0);
        fs_normal = vec4(N * 0.5 + 0.5, 0.0);

        fs_velocity = (vs_output.projection_pos.xy / vs_output.projection_pos.w) - (vs_output.prev_projection_pos.xy / vs_output.prev_projection_pos.w);
        // NDC coord -> Screen Coord
        fs_velocity *= 0.5;
    }
    else
    {
        float shadow_factor = get_shadow_factor(screen_tex_coord, vs_output.world_position, texture_shadow);

        fs_diffuse = surface_shading(base_color,
                        metalicness,
                        get_roughness(),
                        reflectance,
                        texture_cube,
                        texture_scene_reflect,
                        screen_tex_coord,
                        LIGHT_COLOR.xyz,
                        N,
                        V,
                        L,
                        shadow_factor);

        // SSAO
        fs_diffuse.xyz *= texture(texture_ssao, screen_tex_coord).x;

        // Emissive
        fs_diffuse.xyz += emissive_color.xyz * emissive_color.w;
    }
}
#endif