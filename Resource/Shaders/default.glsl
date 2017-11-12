#version 430 core

#define USE_REFLECTION 0

#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "default_material.glsl"
#include "default_vs.glsl"

uniform sampler2D texture_shadow;

//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;

layout (location = 0) out vec4 fs_output;
layout (location = 1) out vec4 fs_diffuse;
layout (location = 2) out vec4 fs_normal;
layout (location = 3) out vec2 fs_velocity;

void main() {
    vec4 base_color = get_base_color(vs_output.tex_coord.xy);

    if(base_color.a < 0.333f && enable_blend != 1)
    {
        discard;
    }

    vec4 emissive_color = get_emissive_color();
    float shadow_factor = get_shadow_factor(vs_output.world_position, texture_shadow);

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
                    LIGHT_COLOR.xyz,
                    N,
                    V,
                    L,
                    shadow_factor);

    fs_output.xyz += emissive_color.xyz * emissive_color.w;
    fs_output = vec4(fs_output.xyz , 1.0);

    fs_diffuse = base_color;

    // because, rendertarget is UNSIGNED_BYTE
    fs_normal = vec4(N, 1.0) * 0.5 + 0.5;
    fs_velocity = (vs_output.projection_pos.xy / vs_output.projection_pos.w) -
        (vs_output.prev_projection_pos.xy / vs_output.prev_projection_pos.w);
}
#endif