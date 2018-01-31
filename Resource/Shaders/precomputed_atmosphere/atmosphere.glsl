#include "PCFKernels.glsl"
#include "utility.glsl"
#include "precomputed_atmosphere/atmosphere_predefine.glsl"
#include "precomputed_atmosphere/atmosphere_vs.glsl"

const vec3 kSphereCenter = vec3(1.0, 1.0, -2.0);
const float kSphereRadius = 1.0;
const vec3 kSphereAlbedo = vec3(0.8);
const vec3 kGroundAlbedo = vec3(0.0, 0.0, 0.04);

uniform vec3 camera;
uniform vec3 earth_center;
uniform vec3 sun_direction;
uniform vec2 sun_size;
uniform float exposure;

uniform sampler2D texture_shadow;
uniform sampler2D texture_depth;
uniform sampler2D texture_normal;
uniform sampler2D transmittance_texture;
uniform sampler3D scattering_texture;
uniform sampler3D single_mie_scattering_texture;
uniform sampler2D irradiance_texture;

uniform vec3 SKY_RADIANCE_TO_LUMINANCE;
uniform vec3 SUN_RADIANCE_TO_LUMINANCE;


vec3 GetSolarRadiance()
{
    return ATMOSPHERE.solar_irradiance /
        (PI * ATMOSPHERE.sun_angular_radius * ATMOSPHERE.sun_angular_radius) *
        SUN_RADIANCE_TO_LUMINANCE;
}

vec3 GetSkyRadiance(
    vec3 camera, vec3 view_ray, float shadow_length,
    vec3 sun_direction, out vec3 transmittance)
{
    return ComputeSkyRadiance(ATMOSPHERE, transmittance_texture,
        scattering_texture, single_mie_scattering_texture,
        camera, view_ray, shadow_length, sun_direction, transmittance) *
        SKY_RADIANCE_TO_LUMINANCE;
}

vec3 GetSkyRadianceToPoint(
    vec3 camera, vec3 point, float shadow_length,
    vec3 sun_direction, out vec3 transmittance)
{
    return ComputeSkyRadianceToPoint(ATMOSPHERE, transmittance_texture,
        scattering_texture, single_mie_scattering_texture,
        camera, point, shadow_length, sun_direction, transmittance) *
        SKY_RADIANCE_TO_LUMINANCE;
}

vec3 GetSunAndSkyIrradiance(
   vec3 p, vec3 normal, vec3 sun_direction,
   out vec3 sky_irradiance)
{
    vec3 sun_irradiance = ComputeSunAndSkyIrradiance(
        ATMOSPHERE, transmittance_texture, irradiance_texture, p, normal,
        sun_direction, sky_irradiance);
    sky_irradiance *= SKY_RADIANCE_TO_LUMINANCE;
    return sun_irradiance * SUN_RADIANCE_TO_LUMINANCE;
}

float GetSunVisibility(vec3 point, vec3 sun_direction)
{
    vec3 p = point - kSphereCenter;
    float p_dot_v = dot(p, sun_direction);
    float p_dot_p = dot(p, p);
    float ray_sphere_center_squared_distance = p_dot_p - p_dot_v * p_dot_v;
    float distance_to_intersection = -p_dot_v - sqrt(
        kSphereRadius * kSphereRadius - ray_sphere_center_squared_distance);
    if (distance_to_intersection > 0.0)
    {
        float ray_sphere_distance = kSphereRadius - sqrt(ray_sphere_center_squared_distance);
        float ray_sphere_angular_distance = -ray_sphere_distance / p_dot_v;
        return smoothstep(1.0, 0.0, ray_sphere_angular_distance / sun_size.x);
    }
    return 1.0;
}

float GetSkyVisibility(vec3 point)
{
  vec3 p = point - kSphereCenter;
  float p_dot_p = dot(p, p);
  return 1.0 + p.y / sqrt(p_dot_p) * kSphereRadius * kSphereRadius / p_dot_p;
}

void GetSphereShadowInOut(vec3 view_direction, vec3 sun_direction, out float d_in, out float d_out)
{
    vec3 pos = camera - kSphereCenter;
    float pos_dot_sun = dot(pos, sun_direction);
    float view_dot_sun = dot(view_direction, sun_direction);
    float k = sun_size.x;
    float l = 1.0 + k * k;
    float a = 1.0 - l * view_dot_sun * view_dot_sun;
    float b = dot(pos, view_direction) - l * pos_dot_sun * view_dot_sun - k * kSphereRadius * view_dot_sun;
    float c = dot(pos, pos) - l * pos_dot_sun * pos_dot_sun -
        2.0 * k * kSphereRadius * pos_dot_sun - kSphereRadius * kSphereRadius;
    float discriminant = b * b - a * c;
    if (discriminant > 0.0)
    {
        d_in = max(0.0, (-b - sqrt(discriminant)) / a);
        d_out = (-b + sqrt(discriminant)) / a;
        float d_base = -pos_dot_sun / view_dot_sun;
        float d_apex = -(pos_dot_sun + kSphereRadius / k) / view_dot_sun;
        if (view_dot_sun > 0.0)
        {
            d_in = max(d_in, d_apex);
            d_out = a > 0.0 ? min(d_out, d_base) : d_base;
        }
        else
        {
            d_in = a > 0.0 ? max(d_in, d_base) : d_base;
            d_out = min(d_out, d_apex);
        }
    }
    else
    {
        d_in = 0.0;
        d_out = 0.0;
    }
}


#ifdef GL_FRAGMENT_SHADER
in vec3 view_ray;
in vec2 uv;
layout(location = 0) out vec4 color;

void main()
{
    color = vec4(0.0, 0.0, 0.0, 1.0);

    float scene_depth = texture(texture_depth, uv).x;
    vec3 scene_point = depth_to_relative_world(uv, scene_depth).xyz;
    vec3 view_direction = normalize(view_ray);
    float lightshaft_fadein_hack = smoothstep(0.02, 0.04, dot(normalize(camera - earth_center), sun_direction));

    float earth_radius = abs(earth_center.y);
    float ratio = 0.1;

    vec3 p;
    float p_dot_v;
    float p_dot_p;
    float squared_radius;
    float sphere_shadow_in = 0.0;
    float sphere_shadow_out = 0.0;

    bool render_ground = false;
    float ground_alpha = 0.0;
    vec3 ground_radiance = vec3(0.0);

    bool render_sphere = false;
    float sphere_alpha = 0.0;
    vec3 sphere_radiance = vec3(0.0);

    // Scene
    float scene_shadow_length = 0.0;
    vec3 scene_radiance = vec3(0.0);
    {
        vec3 normal = normalize(texture(texture_normal, uv).xyz * 2.0 - 1.0);
        vec3 point = (camera + scene_point) * ratio;

        bool shadow_enter = false;
        float s_out = 0.0;
        float s_in = 0.0;
        float d = 0.1;
        vec3 normalized_dir = normalize(scene_point);

        for(int i=0; i<100; ++i)
        {
            vec3 world_pos = camera + normalized_dir * float(i) * d;
            vec4 shadow_uv = SHADOW_MATRIX * vec4(world_pos, 1.0);
            shadow_uv.xyz /= shadow_uv.w;
            shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
            float s = texture(texture_shadow, shadow_uv.xy, 0).x;

            if(false == shadow_enter && s <= shadow_uv.z)
            {
                // Check if the ray enters the earth.
                if(render_ground && length(world_pos - earth_center) < earth_radius)
                {
                    s_in = 0.0;
                    s_out = 0.0;
                    break;
                }

                shadow_enter = true;
                s_in = world_pos.z;
                continue;
            }

            if(shadow_enter && (shadow_uv.z < s || i == 99))
            {
                s_out = world_pos.z;
                break;
            }
        }

        scene_shadow_length = max(0.0, abs(s_out - s_in));

        vec3 sky_irradiance;
        vec3 sun_irradiance = GetSunAndSkyIrradiance( point.xyz - earth_center, normal, sun_direction, sky_irradiance);
        scene_radiance = kSphereAlbedo * (1.0 / PI) * (sun_irradiance + sky_irradiance);

        vec3 transmittance;
        vec3 in_scatter = GetSkyRadianceToPoint(camera - earth_center, point.xyz - earth_center, scene_shadow_length, sun_direction, transmittance);
        scene_radiance = scene_radiance * transmittance + in_scatter;
    }

    // Sphere
    if(render_sphere)
    {
        GetSphereShadowInOut(view_direction, sun_direction, sphere_shadow_in, sphere_shadow_out);

        p = camera - kSphereCenter;
        p_dot_v = dot(p, view_direction);
        p_dot_p = dot(p, p);
        squared_radius = kSphereRadius * kSphereRadius;

        float ray_sphere_center_squared_distance = p_dot_p - p_dot_v * p_dot_v;
        float distance_to_intersection = -p_dot_v - sqrt(kSphereRadius * kSphereRadius - ray_sphere_center_squared_distance);
        float sphere_depth = distance_to_intersection * view_direction.z;

        if (render_sphere && ray_sphere_center_squared_distance <= squared_radius && abs(sphere_depth) < abs(scene_point.z))
        {
            sphere_alpha = 1.0;
            vec3 point = camera + view_direction * distance_to_intersection;
            vec3 normal = normalize(point - kSphereCenter);

            vec4 shadow_uv = SHADOW_MATRIX * vec4(point, 1.0);
            shadow_uv.xyz /= shadow_uv.w;
            shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
            float scene_shadow = texture(texture_shadow, shadow_uv.xy, 0).x < shadow_uv.z ? 0.0 : 1.0;

            vec3 sky_irradiance;
            vec3 sun_irradiance = GetSunAndSkyIrradiance( point - earth_center, normal, sun_direction, sky_irradiance);

            sphere_radiance = kSphereAlbedo * (1.0 / PI) * (sun_irradiance + sky_irradiance) * scene_shadow;

            float shadow_length = max(0.0, min(sphere_shadow_out, distance_to_intersection) - sphere_shadow_in);
            shadow_length = max(scene_shadow_length, shadow_length) * lightshaft_fadein_hack;

            vec3 transmittance;
            vec3 in_scatter = GetSkyRadianceToPoint(
                    camera - earth_center,point - earth_center, shadow_length, sun_direction, transmittance);
            sphere_radiance = sphere_radiance * transmittance + in_scatter;
        }
    }

    // Ground
    if(render_ground)
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
            float scene_shadow = texture(texture_shadow, shadow_uv.xy, 0).x < shadow_uv.z ? 0.0 : 1.0;

            vec3 sky_irradiance;
            vec3 sun_irradiance = GetSunAndSkyIrradiance(point - earth_center, normal, sun_direction, sky_irradiance);

            ground_radiance = kGroundAlbedo * (1.0 / PI) *
                (sun_irradiance * GetSunVisibility(point, sun_direction) +
                sky_irradiance * GetSkyVisibility(point)) * scene_shadow;

            float shadow_length = max(0.0, min(sphere_shadow_out, distance_to_intersection) - sphere_shadow_in);
            shadow_length = max(scene_shadow_length, shadow_length) * lightshaft_fadein_hack;

            vec3 transmittance;
            vec3 in_scatter = GetSkyRadianceToPoint(camera - earth_center, point - earth_center, shadow_length, sun_direction, transmittance);
            ground_radiance = ground_radiance * transmittance + in_scatter;
            ground_alpha = 1.0;
        }
    }

    // Sky
    float shadow_length = max(scene_shadow_length, max(0.0, sphere_shadow_out - sphere_shadow_in)) * lightshaft_fadein_hack;

    vec3 transmittance;
    vec3 radiance = GetSkyRadiance(camera * ratio - earth_center, view_direction, shadow_length, sun_direction, transmittance);

    // Sun
    if (dot(view_direction, sun_direction) > sun_size.y)
    {
        radiance = radiance + transmittance * GetSolarRadiance();
    }

    // Final composite
    radiance = mix(radiance, ground_radiance, ground_alpha);
    radiance = mix(max(vec3(0.0), scene_radiance), radiance, scene_depth > 0.9999 ? 1.0 : 0.0);
    radiance = mix(radiance, sphere_radiance, sphere_alpha);

    color.xyz = radiance * exposure;
    color.w = 1.0;
    color = max(color, 0.0);
}
#endif
