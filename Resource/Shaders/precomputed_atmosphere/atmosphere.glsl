#include "utility.glsl"
#include "precomputed_atmosphere/atmosphere_predefine.glsl"
#include "precomputed_atmosphere/atmosphere_vs.glsl"

uniform sampler2D texture_shadow;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_normal;

#ifdef GL_FRAGMENT_SHADER
in vec3 view_ray;
in vec2 uv;
layout(location = 0) out vec4 color;

void main()
{
    color = vec4(0.0, 0.0, 0.0, 1.0);
    vec3 camera = CAMERA_POSITION.xyz;
    vec3 sun_direction = LIGHT_DIRECTION.xyz;
    vec3 view_direction = normalize(view_ray);

    float lightshaft_fadein_hack = smoothstep(0.02, 0.04, dot(normalize(camera - earth_center), sun_direction));

    // Scene
    float scene_linear_depth = texture(texture_linear_depth, uv).x;
    vec3 normal = normalize(texture(texture_normal, uv).xyz * 2.0 - 1.0);
    float scene_shadow_length = 0.0;
    vec3 scene_radiance = vec3(0.0);
    GetSceneRadiance(
        ATMOSPHERE, scene_linear_depth, view_direction, normal, texture_shadow, scene_radiance, scene_shadow_length);

    float shadow_length = scene_shadow_length * lightshaft_fadein_hack;

    // Sky
    vec3 transmittance;
    vec3 radiance = GetSkyRadiance(
        ATMOSPHERE, camera * atmosphere_ratio - earth_center, view_direction, shadow_length, sun_direction, transmittance);

    // Sun
    if (dot(view_direction, sun_direction) > sun_size.y)
    {
        radiance = radiance + transmittance * GetSolarRadiance(ATMOSPHERE);
    }

    // Final composite
    radiance = mix(scene_radiance, radiance, scene_linear_depth < NEAR_FAR.y ? 0.0 : 1.0);

    color.xyz = radiance * exposure;
    color.w = scene_linear_depth < NEAR_FAR.y ? 0.0 : 1.0;
    color = max(color, 0.0);
}
#endif
