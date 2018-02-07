#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "quad.glsl"
#include "precomputed_atmosphere/atmosphere_predefine.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_material;
uniform sampler2D texture_normal;

uniform sampler2D texture_depth;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_shadow;
uniform sampler2D texture_ssao;
uniform sampler2D texture_scene_reflect;
uniform samplerCube texture_probe;


#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 screen_tex_coord = vs_output.tex_coord.xy;

    float depth = texture(texture_depth, screen_tex_coord).x;

    if(depth == 1.0)
    {
        discard;
    }

    vec4 base_color = texture(texture_diffuse, screen_tex_coord);
    // decoding
    base_color.w *= 10.0;

    vec4 material = texture(texture_material, screen_tex_coord);
    vec3 N = normalize(texture(texture_normal, screen_tex_coord).xyz * 2.0 - 1.0);

    vec4 world_position = vec4(screen_tex_coord * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    world_position = INV_VIEW * INV_PROJECTION * world_position;
    world_position /= world_position.w;

    float roughness = material.x;
    float metalicness = material.y;
    float reflectance = material.z;

    vec3 V = normalize(CAMERA_POSITION.xyz - world_position.xyz);
    vec3 L = normalize(LIGHT_DIRECTION.xyz);

    vec3 shadow_factor = vec3(get_shadow_factor(screen_tex_coord, world_position.xyz, texture_shadow));

    // Atmosphere
    float scene_shadow_length = 0.0;
    vec3 scene_sun_irradiance = vec3(0.0);
    vec3 scene_sky_irradiance = vec3(0.0);
    vec3 scene_in_scatter = vec3(0.0);
    {
        float lightshaft_fadein_hack =
            smoothstep(0.02, 0.04, dot(normalize(CAMERA_POSITION.xyz - earth_center), LIGHT_DIRECTION.xyz));

        // Scene
        vec3 view_direction = normalize(-V);
        float scene_linear_depth = texture(texture_linear_depth, screen_tex_coord).x;
        vec3 normal = normalize(texture(texture_normal, screen_tex_coord).xyz * 2.0 - 1.0);

        GetSceneRadiance(
            ATMOSPHERE, scene_linear_depth, view_direction, normal, texture_shadow,
            scene_sun_irradiance, scene_sky_irradiance, scene_in_scatter, scene_shadow_length);
        scene_sun_irradiance *= exposure;
        scene_sky_irradiance *= exposure;
        scene_in_scatter *= exposure;
        shadow_factor = max(shadow_factor, scene_sky_irradiance);
    }

    fs_output = surface_shading(base_color,
                    metalicness,
                    roughness,
                    reflectance,
                    texture_probe,
                    texture_scene_reflect,
                    screen_tex_coord,
                    LIGHT_COLOR.xyz * scene_sun_irradiance,
                    N,
                    V,
                    L,
                    shadow_factor);

    // SSAO
    if(RENDER_SSAO == 1.0f)
    {
        fs_output.xyz *= texture(texture_ssao, screen_tex_coord).x;
    }

    // emissive
    fs_output.xyz += base_color.xyz * base_color.w + scene_in_scatter;
    fs_output.w = 1.0;
}
#endif