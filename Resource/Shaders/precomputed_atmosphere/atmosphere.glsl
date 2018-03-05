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


float get_cloud_density(vec3 uvw, vec3 cloud_speed)
{
    float distortion = 0.0;//texture(texture_noise, uvw * 0.0051 + cloud_speed * 0.5).x;
    float cloud_density = texture(texture_noise, uvw * 0.0012 - cloud_speed + distortion * 0.05).x;
    return clamp(pow(cloud_density, 10.0) * 2.0, 0.0, 1.0);
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
    vec3 view_direction = normalize(view_ray);

    // Scene
    float scene_shadow_length = GetSceneShadowLength(scene_linear_depth, view_direction, texture_shadow);

    // Sky
    vec3 transmittance;
    vec3 radiance = GetSkyRadiance(
        ATMOSPHERE, camera - earth_center, view_direction, scene_shadow_length, sun_direction, transmittance);

    // Sun
    if (render_sun && dot(view_direction, sun_direction) > sun_size.y)
    {
        radiance = radiance + transmittance * GetSolarRadiance(ATMOSPHERE);
    }

    // Cloud
    vec4 cloud = vec4(0.0);
    const float cloud_height = 200.0;
    const float cloud_thickness = 200.0;
    float height_diff = cloud_height - CAMERA_POSITION.y;
    if(0.0 < view_direction.y && 0.0 < (height_diff + cloud_thickness) || view_direction.y < 0.0 && height_diff < 0.0)
    {
        // relative ray march start pos from the camera
        vec3 ray_start_pos;

        const bool in_the_cloud = -cloud_thickness < height_diff && height_diff < 0.0;

        if(in_the_cloud)
        {
            // be in clouds
            ray_start_pos = vec3(0.0, 0.0, 0.0);
        }
        else if(0.0 < view_direction.y)
        {
            // under the sky
            ray_start_pos = view_direction * abs(height_diff / view_direction.y);
        }
        else
        {
            // above the sky
            ray_start_pos = view_direction * abs((height_diff + cloud_thickness) / view_direction.y);
        }

        float dist = clamp(length(ray_start_pos), 0.0, NEAR_FAR.y);

        ray_start_pos += CAMERA_POSITION.xyz;

        if(dist < NEAR_FAR.y)
        {
            float march_height = cloud_thickness;

            if(0.0 < view_direction.y)
            {
                // Looking up at the sky
                march_height = clamp(cloud_thickness + height_diff, 0.0, cloud_thickness);
            }
            else
            {
                // Looking down at the sky
                march_height = clamp(-height_diff, 0.0, cloud_thickness);
            }

            const float absorption = 0.8;
            const vec3 cloud_color = vec3(0.5, 0.5, 0.7);
            const int march_count = 50;
            const vec3 cloud_speed = vec3(0.03, 0.03, 0.0) * TIME;
            const int light_march_count = 10;

            float march_step = abs(march_height / view_direction.y) / float(march_count);
            // When you are in the clouds, march steps are likely to be too large.
            //if(in_the_cloud)
            {
                march_step = min(march_step, 5.0);
            }

            for(int i=0; i<march_count; ++i)
            {
                vec3 uvw = ray_start_pos.xzy + view_direction.xzy * float(march_count - i) * march_step;
                float cloud_density = get_cloud_density(uvw, cloud_speed);
                vec3 light_color = vec3(1.0, 1.0, 1.0) * LIGHT_COLOR.xyz;

                for(int j=0; j<light_march_count; ++j)
                {
                    vec3 uvw_light = uvw + LIGHT_DIRECTION.xzy * float(light_march_count - j) * march_step;
                    float cloud_density2 = get_cloud_density(uvw_light, cloud_speed);
                    light_color = clamp(light_color * (1.0 - pow(cloud_density2, 0.5) * absorption), 0.0, 1.0);
                }

                cloud.xyz = mix(cloud.xyz, light_color, cloud_density);
                cloud.w = clamp(cloud.w + cloud_density, 0.0, 1.0);
            }

            const float minDist = 100.0;
            cloud.w *= clamp(1.0 - (dist - minDist) / (NEAR_FAR.y - minDist), 0.0, 1.0);
        }
    }

    color.xyz = mix(radiance * exposure, cloud.xyz, cloud.w);
    color.w = 1.0;
    color = max(color, 0.0);
}
#endif
