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
            const int count = 100;
            const float cloud_speed = TIME * 0.03;

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

            float march_step = abs(march_height / view_direction.y) / float(count);
            // When you are in the clouds, march steps are likely to be too large.
            march_step = min(march_step, 5.0);

            const vec3 cloud_color = vec3(0.5, 0.5, 0.7);
            cloud.xyz = cloud_color;

            for(int i=0; i<count; ++i)
            {
                float weight = 1.0 - abs((float(count - i) / float(count)) * 2.0 - 1.0);
                weight = 0.1;
                vec3 uvw = (ray_start_pos.xyz + view_direction.xyz * float(count - i) * march_step);

                float distortion = texture(texture_noise, uvw * 0.0051 + vec3(cloud_speed, 0.0, cloud_speed) * 0.5).x;
                float opacity = texture(texture_noise, uvw * 0.0012 -
                    vec3(cloud_speed, 0.0, cloud_speed) +
                    distortion * 0.05).x;

                opacity = pow(opacity, 15.0 + 5 * clamp(abs(uvw.y * 2.0 - 1.0), 0.0, 1.0));
                opacity = clamp(opacity * 30.0, 0.0, 1.0);

                cloud.xyz = mix(cloud.xyz, cloud_color * (1.0 - cloud.w), opacity * weight);
                cloud.w = clamp(cloud.w + opacity * weight, 0.0, 1.0);
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
