#include "utility.glsl"
#include "precomputed_atmosphere/atmosphere_predefine.glsl"
#include "precomputed_atmosphere/atmosphere_vs.glsl"

uniform sampler2D texture_shadow;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_normal;


#ifdef FRAGMENT_SHADER
in vec3 view_ray;
in vec2 uv;
layout(location = 0) out vec4 color;

void main()
{
    color = vec4(0.0, 0.0, 0.0, 1.0);
    vec3 camera = CAMERA_POSITION.xyz * atmosphere_ratio;
    vec3 sun_direction = LIGHT_DIRECTION.xyz;

    vec3 view_direction = normalize(view_ray);
    float lightshaft_fadein_hack = smoothstep(0.02, 0.04, dot(normalize(camera - earth_center), sun_direction));

    float earth_radius = abs(earth_center.y);

    vec3 p;
    float p_dot_v;
    float p_dot_p;
    float squared_radius;
    float sphere_shadow_in = 0.0;
    float sphere_shadow_out = 0.0;

    // Scene
    float scene_linear_depth = texture2DLod(texture_linear_depth, uv, 0.0).x;
    vec3 scene_point = view_direction * scene_linear_depth * atmosphere_ratio;
    vec3 normal = normalize(texture2D(texture_normal, uv).xyz * 2.0 - 1.0);
    float scene_shadow_length;
    vec3 scene_radiance;
    vec3 scene_sun_irradiance;
    vec3 scene_sky_irradiance;
    vec3 scene_in_scatter;
    GetSceneRadianceWithShadow(
        ATMOSPHERE, scene_linear_depth, view_direction, normal, texture_shadow,
        scene_sun_irradiance, scene_sky_irradiance, scene_in_scatter, scene_shadow_length);
    scene_radiance = scene_sun_irradiance + scene_sky_irradiance + scene_in_scatter;

    // Sphere
    float sphere_alpha = 0.0;
    vec3 sphere_radiance = vec3(0.0);
    {
        GetSphereShadowInOut(view_direction, sun_direction, sphere_shadow_in, sphere_shadow_out);

        p = camera - kSphereCenter;
        p_dot_v = dot(p, view_direction);
        p_dot_p = dot(p, p);
        squared_radius = kSphereRadius * kSphereRadius;

        float ray_sphere_center_squared_distance = p_dot_p - p_dot_v * p_dot_v;
        float distance_to_intersection = -p_dot_v - sqrt(kSphereRadius * kSphereRadius - ray_sphere_center_squared_distance);
        float sphere_depth = distance_to_intersection * view_direction.z;

        if (ray_sphere_center_squared_distance <= squared_radius && abs(sphere_depth) < abs(scene_point.z))
        {
            sphere_alpha = 1.0;
            vec3 point = camera + view_direction * distance_to_intersection;
            vec3 normal = normalize(point - kSphereCenter);

            vec4 shadow_uv = SHADOW_MATRIX * vec4(point, 1.0);
            shadow_uv.xyz /= shadow_uv.w;
            shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
            float scene_shadow = texture2D(texture_shadow, shadow_uv.xy, 0).x < shadow_uv.z ? 0.0 : 1.0;

            vec3 sky_irradiance;
            vec3 sun_irradiance = GetSunAndSkyIrradiance(
                ATMOSPHERE, point - earth_center, normal, sun_direction, sky_irradiance);

            sphere_radiance = kSphereAlbedo * (1.0 / PI) * (sun_irradiance + sky_irradiance) * scene_shadow;

            float shadow_length = max(0.0, min(sphere_shadow_out, distance_to_intersection) - sphere_shadow_in);
            shadow_length = max(scene_shadow_length, shadow_length) * lightshaft_fadein_hack;

            vec3 transmittance;
            vec3 in_scatter = GetSkyRadianceToPoint(
                    ATMOSPHERE, camera - earth_center,point - earth_center, shadow_length, sun_direction, transmittance);
            sphere_radiance = sphere_radiance * transmittance + in_scatter;
        }
    }

    // Ground
    float ground_alpha = 0.0;
    vec3 ground_radiance = vec3(0.0);
    {
        p = camera - earth_center;
        p_dot_v = dot(p, view_direction);
        p_dot_p = dot(p, p);
        squared_radius = earth_radius * earth_radius;

        float ray_earth_center_squared_distance = p_dot_p - p_dot_v * p_dot_v;
        if (p_dot_v <= 0.0 && ray_earth_center_squared_distance <= squared_radius)
        {
            float distance_to_intersection = -p_dot_v - sqrt(squared_radius - ray_earth_center_squared_distance);
            vec3 point = camera + view_direction * distance_to_intersection;
            vec3 normal = normalize(point - earth_center);

            vec4 shadow_uv = SHADOW_MATRIX * vec4(point, 1.0);
            shadow_uv.xyz /= shadow_uv.w;
            shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
            float scene_shadow = texture2D(texture_shadow, shadow_uv.xy, 0).x < shadow_uv.z ? 0.0 : 1.0;

            vec3 sky_irradiance;
            vec3 sun_irradiance = GetSunAndSkyIrradiance(
                ATMOSPHERE, point - earth_center, normal, sun_direction, sky_irradiance);

            ground_radiance = kGroundAlbedo * (1.0 / PI) *
                (sun_irradiance * GetSunVisibility(point, sun_direction) +
                sky_irradiance * GetSkyVisibility(point)) * scene_shadow;

            float shadow_length = max(0.0, min(sphere_shadow_out, distance_to_intersection) - sphere_shadow_in);
            shadow_length = max(scene_shadow_length, shadow_length) * lightshaft_fadein_hack;

            vec3 transmittance;
            vec3 in_scatter = GetSkyRadianceToPoint(
                ATMOSPHERE, camera - earth_center, point - earth_center, shadow_length, sun_direction, transmittance);
            ground_radiance = ground_radiance * transmittance + in_scatter;
            ground_alpha = 1.0;
        }
    }

    // Sky
    float shadow_length = max(scene_shadow_length, max(0.0, sphere_shadow_out - sphere_shadow_in)) * lightshaft_fadein_hack;

    vec3 transmittance;
    vec3 radiance = GetSkyRadiance(
        ATMOSPHERE, camera - earth_center, view_direction, shadow_length, sun_direction, transmittance);

    // Sun
    if (dot(view_direction, sun_direction) > sun_size.y)
    {
        radiance = radiance + transmittance * GetSolarRadiance(ATMOSPHERE);
    }

    // Final composite
    radiance = mix(radiance, ground_radiance, ground_alpha);
    radiance = mix(scene_radiance, radiance, scene_linear_depth < NEAR_FAR.y ? 0.0 : 1.0);
    radiance = mix(radiance, sphere_radiance, sphere_alpha);

    color.xyz = radiance;
    color.w = scene_linear_depth < NEAR_FAR.y ? 0.0 : 1.0;
    color = max(color, 0.0);
}
#endif
