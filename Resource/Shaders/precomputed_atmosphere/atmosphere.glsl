#include "blending.glsl"
#include "utility.glsl"
#include "precomputed_atmosphere/atmosphere_predefine.glsl"
#include "precomputed_atmosphere/atmosphere_vs.glsl"

uniform sampler2D texture_shadow;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_normal;

uniform sampler3D texture_cloud;
uniform sampler3D texture_noise;

uniform float cloud_exposure;
uniform float cloud_altitude;
uniform float cloud_height;
uniform float cloud_speed;
uniform float cloud_absorption;

uniform float cloud_tiling;
uniform float cloud_contrast;
uniform float cloud_coverage;

uniform float noise_tiling;
uniform float noise_contrast;
uniform float noise_coverage;

#ifdef FRAGMENT_SHADER
in vec3 eye_ray;
in vec2 uv;
layout(location = 0) out vec4 out_color;
layout(location = 1) out vec4 out_inscatter;


float get_cloud_density(vec3 cloud_scale, vec3 noise_scale, vec3 uvw, vec3 speed, float weight)
{
    uvw.xy += CAMERA_POSITION.xz;

    float cloud = texture3D(texture_cloud, uvw * cloud_scale + speed * cloud_tiling / noise_tiling).x;
    cloud = saturate(Contrast((cloud - 1.0 + cloud_coverage), cloud_contrast));

    float noise = texture3D(texture_noise, uvw * noise_scale + speed * 0.3).x;
    noise = saturate(Contrast((noise - 1.0 + noise_coverage) * weight, noise_contrast));

    // Remap is very important!!
    return saturate(Remap(noise, 1.0 - cloud, 1.0, 0.0, 1.0));
}

void main()
{
    out_color = vec4(0.0, 0.0, 0.0, 1.0);

    const float min_dist = 1000.0;
    const float far_dist = NEAR_FAR.y * 4.0;

    vec3 camera = vec3(0.0, max(10.0, CAMERA_POSITION.y), 0.0) * atmosphere_ratio;

    float world_pos_y = max(0.0, CAMERA_POSITION.y);

    vec3 sun_direction = LIGHT_DIRECTION.xyz;
    vec3 eye_direction = normalize(eye_ray);
    vec3 screen_center_ray = -vec3(VIEW_ORIGIN[0].z, VIEW_ORIGIN[1].z, VIEW_ORIGIN[2].z);
    float VdotL = dot(eye_direction, sun_direction);

    float scene_linear_depth = texture2DLod(texture_linear_depth, uv, 0.0).x;
    float scene_dist = clamp(scene_linear_depth / dot(screen_center_ray, eye_direction), 0.0, NEAR_FAR.y);
    float scene_shadow_length = GetSceneShadowLength(scene_dist, eye_direction, texture_shadow);

    // Sky
    vec3 transmittance;
    vec3 radiance = GetSkyRadiance(ATMOSPHERE, camera - earth_center, eye_direction, scene_shadow_length, sun_direction, transmittance);

    // Sun
    vec3 sun_disc = vec3(0.0);
    vec3 solar_radiance = GetSolarRadiance(ATMOSPHERE);
    const float sun_absorption = 0.9;
    const float sun_intensity = 1.0;
    if (!render_light_probe_mode && sun_size.y < VdotL)
    {
        sun_disc = transmittance * solar_radiance * pow(clamp((VdotL - sun_size.y) / (1.0 - sun_size.y), 0.0, 1.0), 2.0);
        sun_disc *= LIGHT_COLOR.xyz * sun_intensity;
        radiance += sun_disc * sun_absorption;
    }

    // Cloud
    vec4 cloud = vec4(0.0);
    vec3 earth_center_pos = earth_center / atmosphere_ratio;

    // distance from earch center
    const float cloud_bottom_dist = cloud_altitude - earth_center_pos.y;
    const float cloud_top_dist = cloud_bottom_dist + cloud_height;
    float altitude_diff = cloud_altitude - world_pos_y;
    const bool in_the_cloud = -cloud_height < altitude_diff && altitude_diff < 0.0;
    bool above_the_cloud = false;
    bool render_cloud = true;

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
        vec3 to_origin = vec3(0.0, world_pos_y, 0.0) - earth_center_pos;
        float c = pow(dot(eye_direction, to_origin), 2.0) - dot(to_origin, to_origin);

        if(cloud_altitude < world_pos_y)
        {
            // above the sky
            if(eye_direction.y < 0.0)
            {
                // look down
                c = -sqrt(c + cloud_top_dist * cloud_top_dist);
                above_the_cloud = true;
            }
            else
            {
                // look up, discard
                render_cloud = false;
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

    // apply altitude of camera
    ray_start_pos.y += world_pos_y;

    // vec3 smooth_N = normalize(ray_start_pos.xyz - earth_center);
    vec3 N = normalize(ray_start_pos.xyz);

    float altitude_ratio = saturate(world_pos_y / (cloud_altitude + cloud_height));
    float atmosphere_lighting = max(0.2, pow(saturate(dot(N, sun_direction) * 0.5 + 0.5), 1.0));

    // Cloud
    if(render_cloud)
    {
        vec3 cloud_inscatter = vec3(0.0);
        vec3 cloud_sun_irradiance = vec3(0.0);
        vec3 cloud_sky_irradiance = vec3(0.0);

        // NOTE : 0.1 is more colorful scattering cloud.
        float dist_to_point = hit_dist * (above_the_cloud ? 1.0 : 0.01);

        GetCloudRadiance(ATMOSPHERE, dist_to_point, eye_direction, scene_shadow_length,
            cloud_sun_irradiance, cloud_sky_irradiance, cloud_inscatter);

        if(in_the_cloud || above_the_cloud)
        {
            cloud_inscatter = vec3(0.0);
        }

        vec3 light_color = cloud_sun_irradiance + cloud_sky_irradiance;
        light_color *= cloud_exposure * LIGHT_COLOR.xyz * atmosphere_lighting;

        if(0.0 <= hit_dist && hit_dist < far_dist)
        {
            const vec3 speed = vec3(cloud_speed, cloud_speed, 0.0) * TIME;

            vec3 cloud_scale = textureSize(texture_cloud, 0);
            cloud_scale = max(cloud_scale.x, max(cloud_scale.y, cloud_scale.z)) / cloud_scale;
            cloud_scale *= cloud_tiling;

            vec3 noise_scale = textureSize(texture_noise, 0);
            noise_scale = max(noise_scale.x, max(noise_scale.y, noise_scale.z)) / noise_scale;
            noise_scale *= noise_tiling;

            // float view_angle = in_the_cloud ? 0.0 : pow(abs(eye_direction.y), 0.2);
            float march_count = 128.0;
            float light_march_count = 32.0;
            float march_step = cloud_height / march_count;
            float cloud_march_step = march_step;
            float increase_march_step = march_step * 0.03;

            for(int i=0; i<int(march_count); ++i)
            {
                vec3 ray_pos;
                ray_pos = ray_start_pos.xyz + eye_direction.xyz * float(i) * cloud_march_step;

                // fade top and bottom
                float relative_altitude = length(ray_pos - earth_center_pos.xyz) - cloud_bottom_dist;

                if(cloud_height < relative_altitude || relative_altitude < 0.0)
                {
                    continue;
                }

                float fade = saturate(relative_altitude / cloud_height);
                fade = 1.0 - pow(abs(fade * 2.0 - 1.0), 3.0);

                float cloud_density = get_cloud_density(cloud_scale, noise_scale, ray_pos.xzy, speed, fade);

                if(cloud_density <= 0.01)
                {
                    // increase march step
                    cloud_march_step += increase_march_step;
                    continue;
                }
                else
                {
                    // NOTE : decrease is more detail, but not natural.
                    // cloud_march_step = max(march_step, cloud_march_step - increase_march_step * 0.5);
                }

                float light_intensity = 1.0;

                for(int j=0; j<light_march_count; ++j)
                {
                    vec3 light_pos = ray_pos + sun_direction * float(light_march_count - j) * march_step;
                    relative_altitude = length(light_pos.xyz - earth_center_pos.xyz) - cloud_bottom_dist;

                    if(cloud_height < relative_altitude || relative_altitude < 0.0)
                    {
                        continue;
                    }

                    fade = 1.0 - pow(abs(saturate(relative_altitude / cloud_height) * 2.0 - 1.0), 3.0);

                    float light_density = get_cloud_density(cloud_scale, noise_scale, light_pos.xzy, speed, fade);

                    if(light_density <= 0.01)
                    {
                        continue;
                    }

                    light_intensity *= (1.0 - light_density * cloud_absorption);

                    if(light_intensity <= 0.01)
                    {
                        light_intensity = 0.0;
                        break;
                    }
                }

                cloud.xyz += cloud_density * light_color * light_intensity;

                cloud.w = clamp(cloud.w + cloud_density * cloud_absorption, 0.0, 1.0);

                if(1.0 <= cloud.w)
                {
                    break;
                }
            }

            float horizontal_line = pow(saturate(((N.y * 0.5 + 0.5) - 0.49) * 30.0), 0.1);
            cloud.w *= horizontal_line;
        }

        out_color.xyz += max(vec3(0.0), mix(radiance, cloud.xyz, cloud.w));
        out_color.xyz += sun_disc * saturate(1.0 - cloud.w);
        out_color.w = clamp(cloud.w, 0.0, 1.0);
    }


    vec3 far_point = camera + eye_direction.xyz * max(NEAR_FAR.x, scene_dist) * atmosphere_ratio;
    vec3 scene_transmittance;
    vec3 scene_inscatter = GetSkyRadianceToPoint(
        ATMOSPHERE, camera - earth_center, far_point.xyz - earth_center, scene_shadow_length, LIGHT_DIRECTION.xyz, scene_transmittance);
    scene_inscatter = max(vec3(0.0), scene_inscatter);

    if(render_light_probe_mode)
    {
        out_color.xyz += scene_inscatter;
    }

    if(render_cloud)
    {
        out_inscatter.xyz += scene_inscatter;
    }
}
#endif
