#include "utility.glsl"
#include "precomputed_atmosphere/atmosphere_predefine.glsl"
#include "precomputed_atmosphere/atmosphere_vs.glsl"

uniform sampler2D texture_shadow;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_normal;

#ifdef MATERIAL_COMPONENTS
    uniform sampler3D texture_noise;
#endif

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
    vec3 relative_point = relative_camera_pos + eye_direction * max(NEAR_FAR.x, dist) * atmosphere_ratio;
    vec3 N = normalize(relative_point - earth_center);

    sun_irradiance = GetSunAndSkyIrradiance(
        atmosphere, relative_point.xyz - earth_center, N, sun_direction, sky_irradiance);

    vec3 transmittance;
    in_scatter = GetSkyRadianceToPoint(atmosphere, relative_camera_pos - earth_center,
        relative_point.xyz - earth_center, scene_shadow_length, sun_direction, transmittance);

    sun_irradiance *= transmittance / PI;
    sky_irradiance *= transmittance / PI;
}


float get_cloud_density(vec3 uvw, vec3 cloud_speed, float weight)
{
    uvw.xy += CAMERA_POSITION.xz;
    float distortion = 0.0;//texture(texture_noise, uvw * 0.0051 + cloud_speed * 0.5).x;
    float cloud_density = texture(texture_noise, uvw * 0.0012 - cloud_speed + distortion * 0.05).x;
    cloud_density *= weight;
    return clamp((cloud_density - 0.6) * 40.0, 0.0, 1.0);
    //return clamp(pow(cloud_density, 10.0) * 2.0, 0.0, 1.0);
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
        radiance = radiance + transmittance * GetSolarRadiance(ATMOSPHERE);
    }

    // Cloud
    vec4 cloud = vec4(0.0);
    const float cloud_height = 500.0;
    const float cloud_thickness = 300.0;
    const float min_dist = 1000.0;
    const float far_dist = NEAR_FAR.y * 2.0;

    // multiply atmosphere_ratio is correct but looking good.
    vec3 earth_center_pos = earth_center / (cloud_height < CAMERA_POSITION.y ? atmosphere_ratio : 0.5);

    const float cloud_bottom_height = cloud_height - earth_center_pos.y;
    const float cloud_top_height = cloud_bottom_height + cloud_thickness;
    float height_diff = cloud_height - CAMERA_POSITION.y;
    const bool in_the_cloud = -cloud_thickness < height_diff && height_diff < 0.0;

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

            if(cloud_height < CAMERA_POSITION.y)
            {
                // above the sky
                if(eye_direction.y < 0.0)
                {
                    // look down
                    c = -sqrt(c + cloud_top_height * cloud_top_height);
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
                float r = cloud_height - earth_center_pos.y;
                c = sqrt(c + cloud_bottom_height * cloud_bottom_height);
            }

            hit_dist = -dot(eye_direction, to_origin) + c;
            ray_start_pos = eye_direction * hit_dist;
        }

        // Atmosphere
        vec3 scene_radiance = vec3(0.0);
        vec3 scene_in_scatter = vec3(0.0);
        vec3 scene_sun_irradiance;
        vec3 scene_sky_irradiance;
        {
            float scene_shadow_length = 0.0;
            GetSceneRadiance(
                ATMOSPHERE, hit_dist, eye_direction, scene_shadow_length,
                scene_sun_irradiance, scene_sky_irradiance, scene_in_scatter);
            scene_radiance = (scene_sun_irradiance + scene_sky_irradiance + scene_in_scatter) * exposure;
            scene_sky_irradiance *= exposure;
            scene_in_scatter *= exposure;
        }

        // apply altitude of camera
        ray_start_pos.y += CAMERA_POSITION.y;

        float dist_fade = clamp(1.0 - (hit_dist - min_dist) / (far_dist - min_dist), 0.0, 1.0);
        cloud.xyz = vec3(1.0, 1.0, 1.0) * LIGHT_COLOR.xyz * scene_radiance;

        if(0.0 <= hit_dist && hit_dist < far_dist)
        {
            const float opacity_absorption = 0.5;
            const float light_absorption = 0.2;
            const vec3 cloud_color = vec3(0.5, 0.5, 0.7);
            const int march_count = 30;
            const vec3 cloud_speed = vec3(0.03, 0.03, 0.0) * TIME;
            const vec3 light_color = vec3(1.0, 1.0, 1.0) * LIGHT_COLOR.xyz * scene_radiance;
            const int light_march_count = 5;
            const bool inverse_ray_march = false;

            float march_step = cloud_thickness / float(march_count);

            for(int i=0; i<march_count; ++i)
            {
                vec3 uvw;
                if(inverse_ray_march)
                {
                    uvw = ray_start_pos.xzy + eye_direction.xzy * float(march_count - i) * march_step;
                }
                else
                {
                    uvw = ray_start_pos.xzy + eye_direction.xzy * float(i) * march_step;
                }

                float weight = (length(uvw.xzy - earth_center_pos.xyz) - cloud_bottom_height) / cloud_thickness;
                weight = pow(clamp((1.0 - abs(weight * 2.0 - 1.0)) * 5.0, 0.0, 1.0), 0.1);
                float cloud_density = get_cloud_density(uvw, cloud_speed, weight);

                float light_intensity = 1.0;
                for(int j=1; j<light_march_count; ++j)
                {
                    vec3 uvw_light = uvw + sun_direction.xzy * float(j) * march_step;
                    float d = length(uvw_light.xzy - earth_center_pos.xyz) - cloud_bottom_height;
                    if(cloud_thickness < d || d < 0.0)
                    {
                        break;
                    }

                    float light_density = get_cloud_density(uvw_light, cloud_speed, 1.0);
                    light_intensity *= 1.0 - light_density * light_absorption;
                    if(light_intensity <= 0.01)
                    {
                        break;
                    }
                }

                if(inverse_ray_march)
                {
                    cloud.xyz = mix(cloud.xyz, light_color * light_intensity, cloud_density);
                    cloud.w = clamp(cloud.w + cloud_density, 0.0, 1.0);
                }
                else
                {
                    cloud.w = clamp(cloud.w + cloud_density, 0.0, 1.0);
                    cloud.xyz = mix(light_color * light_intensity, cloud.xyz, cloud.w);
                    if(1.0 <= cloud.w)
                    {
                        break;
                    }
                }
            }
            cloud.w *= dist_fade;
        }
    }



    color.xyz = mix(radiance * exposure, cloud.xyz, cloud.w);
    color.w = 1.0;
    color = max(color, 0.0);
}
#endif
