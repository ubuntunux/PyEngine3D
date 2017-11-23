#version 430 core

#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "default_material.glsl"
#include "default_vs.glsl"

uniform sampler2D texture_depth;
uniform sampler2D texture_shadow;
uniform sampler2D texture_scene_reflect;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 screen_tex_coord = vs_output.projection_pos.xy / vs_output.projection_pos.w * 0.5 + 0.5;
    float depth = texture(texture_depth, screen_tex_coord).x;

    // discard for early-z.
    const float Epsilon = 0.00001;
    if(depth < gl_FragCoord.z - Epsilon)
    {
        discard;
    }

    vec4 base_color = get_base_color(vs_output.tex_coord.xy);

#if TRANSPARENT_MATERIAL == 1
    base_color.a *= opacity;
#endif

#if TRANSPARENT_MATERIAL != 1
    if(base_color.a < 0.333f)
    {
        discard;
    }
#endif

    vec4 emissive_color = get_emissive_color();
    float shadow_factor = get_shadow_factor(screen_tex_coord, vs_output.world_position, texture_shadow);

    vec3 N = get_normal(vs_output.tex_coord.xy);
    // Note : Normalization is very important because tangent_to_world may have been scaled..
    N = normalize((vs_output.tangent_to_world * vec4(N, 0.0)).xyz);
    vec3 V = normalize(CAMERA_POSITION.xyz - vs_output.world_position);
    vec3 L = normalize(LIGHT_DIRECTION.xyz);

    fs_output = surface_shading(base_color,
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

    fs_output.xyz += emissive_color.xyz * emissive_color.w;
}
#endif