#include "blending.glsl"
#include "utility.glsl"
#include "precomputed_atmosphere/atmosphere_predefine.glsl"
#include "precomputed_atmosphere/atmosphere_vs.glsl"

uniform sampler2D texture_shadow;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_normal;

uniform sampler3D texture_cloud;
uniform sampler3D texture_noise;

uniform float cloud_altitude;
uniform float cloud_height;
uniform float cloud_speed;

uniform float cloud_tiling;
uniform float cloud_contrast;
uniform float cloud_coverage;
uniform float cloud_absorption;

uniform float noise_tiling;
uniform float noise_contrast;
uniform float noise_coverage;

#ifdef GL_FRAGMENT_SHADER
in vec3 view_ray;
in vec2 uv;
layout(location = 0) out vec4 color;


void GetSceneRadiance(
    const in AtmosphereParameters atmosphere,
    float dist, vec3 eye_direction, float scene_shadow_length,
    out vec3 sun_irradiance, out vec3 sky_irradiance, out vec3 in_scatter)
{
    vec3 sun_direction = LIGHT_DIRECTION.xyz;
    vec3 relative_camera_pos = CAMERA_POSITION.xyz * atmosphere_ratio;
    vec3 relative_point = relative_camera_pos + eye_direction.xyz * max(NEAR_FAR.x, dist) * atmosphere_ratio;
    vec3 N = normalize(relative_point - earth_center);

    sun_irradiance = GetSunAndSkyIrradiance(
        atmosphere, relative_point.xyz - earth_center, N, sun_direction, sky_irradiance);

    vec3 transmittance;
    in_scatter = GetSkyRadianceToPoint(atmosphere, relative_camera_pos - earth_center,
        relative_point.xyz - earth_center, scene_shadow_length, sun_direction, transmittance);

    sun_irradiance *= transmittance / PI;
    sky_irradiance *= transmittance / PI;
}


float get_cloud_density(vec3 cloud_scale, vec3 noise_scale, vec3 uvw, vec3 speed, float weight)
{
    uvw.xy += CAMERA_POSITION.xz;

    float cloud = texture(texture_cloud, uvw * cloud_scale + speed * cloud_tiling / noise_tiling).x;
    cloud = saturate(Contrast((cloud - 1.0 + cloud_coverage), cloud_contrast));

    float noise = texture(texture_noise, uvw * noise_scale + speed * 0.3).x;
    noise = saturate(Contrast((noise - 1.0 + noise_coverage) * weight, noise_contrast));

    // Remap is very important!!
    return saturate(Remap(noise, 1.0 - cloud, 1.0, 0.0, 1.0));
}

void main()
{
    float scene_linear_depth = textureLod(texture_linear_depth, uv, 0.0).x;

    if(scene_linear_depth < NEAR_FAR.y)
    {
        discard;
    }

    color = vec4(0.0, 0.0, 0.0, 1.0);
    vec3 camera = CAMERA_POSITION.xyz * atmosphere_ratio;
    vec3 sun_direction = LIGHT_DIRECTION.xyz;
    vec3 eye_direction = normalize(view_ray);

    // Scene
    float scene_shadow_length = GetSceneShadowLength(scene_linear_depth, eye_direction, texture_shadow);

    // Sky
    vec3 transmittance;
    vec3 radiance = GetSkyRadiance(
        ATMOSPHERE, camera - earth_center, eye_direction, scene_shadow_length, sun_direction, transmittance);

    // Sun
    if (render_sun && dot(eye_direction, sun_direction) > sun_size.y)
    {
        radiance += transmittance * GetSolarRadiance(ATMOSPHERE);
    }

    // Cloud
    vec4 cloud = vec4(0.0);
    const float min_dist = 1000.0;
    const float far_dist = NEAR_FAR.y * 4.0;

    vec3 earth_center_pos = earth_center / atmosphere_ratio;

    // distance from earch center
    const float cloud_bottom_dist = cloud_altitude - earth_center_pos.y;
    const float cloud_top_dist = cloud_bottom_dist + cloud_height;
    float altitude_diff = cloud_altitude - CAMERA_POSITION.y;
    const bool in_the_cloud = -cloud_height < altitude_diff && altitude_diff < 0.0;

    {
        // relative ray march start pos from the camera
        vec3 ray_start_pos;
        float hit_dist;

        if(in_the_cloud)
        {
            // be in clouds
            ray_start_pos = vec3(0.0, 0.0, 0.0);
            hit_dist = 0.0;
        }
        else
        {
            // https://en.wikipedia.org/wiki/Line%E2%80%93sphere_intersection

            vec3 to_origin = vec3(0.0, CAMERA_POSITION.y, 0.0) - earth_center_pos;
            float c = pow(dot(eye_direction, to_origin), 2.0) - dot(to_origin, to_origin);

            if(cloud_altitude < CAMERA_POSITION.y)
            {
                // above the sky
                if(eye_direction.y < 0.0)
                {
                    // look down
                    c = -sqrt(c + cloud_top_dist * cloud_top_dist);
                }
                else
                {
                    // look up, discard
                    discard;
                }
            }
            else
            {
                // under the sky
                float r = cloud_altitude - earth_center_pos.y;
                c = sqrt(c + cloud_bottom_dist * cloud_bottom_dist);
            }

            hit_dist = -dot(eye_direction, to_origin) + c;
            ray_start_pos = eye_direction * hit_dist;
        }

        // Atmosphere
        vec3 scene_in_scatter;
        vec3 scene_sun_irradiance;
        vec3 scene_sky_irradiance;
        {
            float scene_shadow_length = 0.0;
            GetSceneRadiance(
                ATMOSPHERE, hit_dist, -eye_direction, scene_shadow_length,
                scene_sun_irradiance, scene_sky_irradiance, scene_in_scatter);
            scene_sun_irradiance = scene_sun_irradiance * exposure;
            scene_sky_irradiance *= exposure;
            scene_in_scatter *= exposure;
        }

        // apply altitude of camera
        ray_start_pos.y += CAMERA_POSITION.y;

        const vec3 light_color = LIGHT_COLOR.xyz * (scene_sun_irradiance + scene_sky_irradiance);

        cloud.xyz = light_color;
        cloud.w = 0.0;

        if(0.0 <= hit_dist && hit_dist < far_dist)
        {
            const float march_count_min = 32.0;
            const float march_count = mix(march_count_min * 2.0, march_count_min, abs(eye_direction.y));
            const float light_march_count = 8.0;
            const float march_step = cloud_height / march_count_min * 2.0;
            const vec3 speed = vec3(cloud_speed, cloud_speed, 0.0) * TIME;

            vec3 cloud_scale = textureSize(texture_cloud, 0);
            cloud_scale = max(cloud_scale.x, max(cloud_scale.y, cloud_scale.z)) / cloud_scale;
            cloud_scale *= cloud_tiling;

            vec3 noise_scale = textureSize(texture_noise, 0);
            noise_scale = max(noise_scale.x, max(noise_scale.y, noise_scale.z)) / noise_scale;
            noise_scale *= noise_tiling;

            for(int i=0; i<int(march_count); ++i)
            {
                vec3 ray_pos;
                ray_pos = ray_start_pos.xyz + eye_direction.xyz * float(i) * march_step;

                // fade top and bottom
                float relative_altitude = length(ray_pos - earth_center_pos.xyz) - cloud_bottom_dist;

                if(0 != i && (cloud_height < relative_altitude || relative_altitude < 0.0))
                {
                    break;
                }

                float fade = saturate(relative_altitude / cloud_height);
                fade = 1.0 - pow(abs(fade * 2.0 - 1.0), 3.0);

                float cloud_density = get_cloud_density(cloud_scale, noise_scale, ray_pos.xzy, speed, fade);

                float light_intensity = 1.0;

                for(int j=0; j<light_march_count; ++j)
                {
                    vec3 light_pos = ray_pos + sun_direction * float(light_march_count - j) * march_step;
                    relative_altitude = length(light_pos.xyz - earth_center_pos.xyz) - cloud_bottom_dist;

                    if(cloud_height < relative_altitude || relative_altitude < 0.0)
                    {
                        break;
                    }

                    fade = 1.0 - pow(abs(saturate(relative_altitude / cloud_height) * 2.0 - 1.0), 3.0);

                    float light_density = get_cloud_density(cloud_scale, noise_scale, light_pos.xzy, speed, fade);

                    light_intensity = saturate(light_intensity - light_density * cloud_absorption);

                    if(light_intensity <= 0.01)
                    {
                        light_intensity = 0.0;
                        break;
                    }
                }

                cloud.xyz += light_color * light_intensity * (1.0 - cloud.w);
                cloud.w = clamp(cloud.w + cloud_density * cloud_absorption, 0.0, 1.0);

                if(1.0 <= cloud.w)
                {
                    break;
                }
            }

            float dist_fade = clamp(1.0 - (hit_dist - min_dist) / (far_dist - min_dist), 0.0, 1.0);
            cloud.w *= clamp(dist_fade, 0.0, 1.0);
        }
        cloud.xyz *= 0.02;
        cloud.xyz += scene_in_scatter;
    }

    color.xyz = mix(radiance * exposure, cloud.xyz, cloud.w);
    color.w = 1.0;
    color = max(color, 0.0);
}
#endif
