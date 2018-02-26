#include "ocean_vs.glsl"
#include "shading.glsl"

uniform sampler2D texture_depth;
uniform sampler2D texture_shadow;
uniform sampler2D texture_scene_reflect;
uniform samplerCube texture_probe;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 uv = vs_output.tex_coord.xy;
    vec2 screen_tex_coord = (vs_output.proj_pos.xy / vs_output.proj_pos.w) * 0.5 + 0.5;
    vec3 front = vec3(VIEW_ORIGIN[0].z, VIEW_ORIGIN[1].z, VIEW_ORIGIN[2].z);
    vec3 relative_pos = CAMERA_POSITION.xyz - vs_output.world_pos.xyz;

    vec3 N = normalize(vs_output.wave_normal);
    vec3 V = normalize(relative_pos);
    vec3 L = LIGHT_DIRECTION.xyz;
    vec3 H = normalize(V + L);
    vec3 R = reflect(-V, N);
    R.y = abs(R.y);

    float NdL = max(0.0, dot(N, L));
    float NdV = max(0.001, dot(N, V));
    float NdH = max(0.001, dot(N, H));
    float HdV = max(0.001, dot(H, V));
    float LdV = max(0.001, dot(L, V));

    const float metallic = 0.0;
    const float roughness = 0.0;

    /////////////////////////////////////////
    float ocean_linear_depth = dot(relative_pos, front);
    float scene_linear_depth = depth_to_linear_depth(texture(texture_depth, screen_tex_coord).x);
    vec4 scene_reflect_color = texture(texture_scene_reflect, screen_tex_coord);
    vec3 foam = texture(texture_foam, uv * uv_tiling).xyz;
    vec3 ocean_color = vec3(1.0, 1.0, 1.0);
    float peak = clamp(vs_output.wave_offset.y, 0.0, 1.0);
    vec3 base_color = mix(ocean_color, foam, peak);
    float depth_diff = clamp(abs(scene_linear_depth - ocean_linear_depth) * 0.5, 0.0, 1.0);

    vec3 shadow_factor = vec3( get_shadow_factor(screen_tex_coord, vs_output.world_pos, texture_shadow) );

    // Atmosphere
    vec3 ocean_radiance = vec3(0.0);
    vec3 ocean_in_scatter = vec3(0.0);
    vec3 ocean_sun_irradiance;
    vec3 ocean_sky_irradiance;
    float ocean_shadow_length;
    {
        GetSceneRadiance(
            ATMOSPHERE, ocean_linear_depth, -V, N, texture_shadow,
            ocean_sun_irradiance, ocean_sky_irradiance, ocean_in_scatter, ocean_shadow_length);
        ocean_radiance = (ocean_sun_irradiance + ocean_sky_irradiance + ocean_in_scatter) * exposure;
        ocean_sky_irradiance *= exposure;
        ocean_in_scatter *= exposure;
    }

    vec3 light_color = LIGHT_COLOR.xyz * ocean_radiance;

    // Fresnel specular reflectance at normal incidence
    const float ior = 1.333;
    vec3 f0 = vec3(abs((1.0 - ior) / (1.0 + ior)));
    vec3 specfresnel = fresnel_factor(f0, abs(HdV));

    // diffuse
    vec3 diffuse_light = vec3(NdL * 0.5 + 0.5);
    diffuse_light = diffuse_light * base_color.xyz * (vec3(1.0) - specfresnel) * light_color * shadow_factor;

    vec3 specular_lighting = vec3(pow(clamp(dot(H, N), 0.0, 1.0), 30.0)) * light_color * NdL * shadow_factor;

    // Image based lighting
    const vec2 env_size = textureSize(texture_probe, 0);
    const float env_mipmap_count = log2(min(env_size.x, env_size.y));

    vec3 ibl_diffuse_color = textureLod(texture_probe, invert_y(N), env_mipmap_count - 1.0).xyz;
    vec3 ibl_specular_color = textureLod(texture_probe, invert_y(R), env_mipmap_count * roughness).xyz;

    // mix scene reflection
    if(RENDER_SSR == 1.0f)
    {
        ibl_specular_color.xyz = mix(ibl_specular_color.xyz, scene_reflect_color.xyz, scene_reflect_color.w);
    }

    diffuse_light += base_color.xyz * ibl_diffuse_color * max(shadow_factor, ocean_sky_irradiance);
    vec2 envBRDF = clamp(env_BRDF_pproximate(NdV, roughness), 0.0, 1.0);
    specular_lighting += (fresnel_factor(f0, NdV) * envBRDF.x + envBRDF.y) * ibl_specular_color * max(shadow_factor, ocean_sky_irradiance);

    // final result
    fs_output.xyz = diffuse_light * (1.0 - metallic) + specular_lighting + ocean_in_scatter;
    fs_output.xyz = mix(fs_output.xyz, ocean_in_scatter, ocean_linear_depth / NEAR_FAR.y);
    fs_output.a = depth_diff;
    /////////////////////////////////////
}
#endif // GL_FRAGMENT_SHADER
