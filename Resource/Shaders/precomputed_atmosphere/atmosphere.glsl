#include "utility.glsl"
#include "precomputed_atmosphere/atmosphere_predefine.glsl"
#include "precomputed_atmosphere/atmosphere_vs.glsl"

uniform sampler2D texture_shadow;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_normal;

#ifdef MATERIAL_COMPONENTS
    uniform sampler2D texture_noise;
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
    float cloud_height = 100.0;
    float height_diff = cloud_height - CAMERA_POSITION.y;
    if(0.0 < view_direction.y && 0.0 < height_diff || view_direction.y < 0.0 && height_diff < 0.0)
    {
        vec3 cloud_pos = view_direction / view_direction.y * height_diff;

        float dist = clamp(length(cloud_pos), 0.0, NEAR_FAR.y);

        cloud_pos.xz += CAMERA_POSITION.xz;

        if(dist < NEAR_FAR.y)
        {
            const int count = 50;
            const float dist_step = dist / height_diff * 1.0;
            const float cloud_pow = 5.0;
            const float cloud_speed = 0.5;
            const vec3 cloud_color = vec3(0.5, 0.5, 0.7);

            cloud.xyz = cloud_color;

            for(int i=0; i<count; ++i)
            {
                vec2 uv = (cloud_pos.xz + view_direction.xz * float(count - i) * dist_step) * 0.001;
                vec2 distortion = texture(texture_noise, uv * 3.5 - vec2(TIME * 0.03), 0.0).xy;
                float opacity = texture(texture_noise, uv + vec2(TIME * 0.02) + distortion * 0.1, 0.0).x;
                const float sharpen = 0.3;
                opacity = clamp((opacity - sharpen) / (1.0 - sharpen), 0.0, 1.0);
                opacity = pow(opacity, cloud_pow);
                cloud.xyz = mix(cloud.xyz, cloud_color * (1.0 - cloud.w * 0.9), opacity);
                cloud.w = clamp(cloud.w + opacity, 0.0, 1.0);
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
