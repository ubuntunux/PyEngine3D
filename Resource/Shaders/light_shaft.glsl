#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_random;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_shadow;
uniform float light_shaft_intensity;
uniform float light_shaft_threshold;
uniform float light_shaft_length;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec2 uv = vs_output.tex_coord;
    vec3 eye_direction = normalize(depth_to_relative_world(uv, 0.0).xyz);
    vec3 screen_center_ray = -vec3(VIEW_ORIGIN[0].z, VIEW_ORIGIN[1].z, VIEW_ORIGIN[2].z);
    float scene_linear_depth = textureLod(texture_linear_depth, uv, 0.0).x;
    float scene_dist = clamp(scene_linear_depth / dot(screen_center_ray, eye_direction), 0.0, NEAR_FAR.y);

    // light shaft color
    vec4 light_shaft_proj = PROJECTION * VIEW_ORIGIN * vec4(LIGHT_DIRECTION.xyz * NEAR_FAR.y, 1.0);
    light_shaft_proj.xyz /= light_shaft_proj.w;
    vec2 light_shaft_uv = light_shaft_proj.xy * 0.5 + 0.5;
    vec2 uv_dir = light_shaft_uv - uv;
    float radian = atan((0.0 != uv_dir.x) ? (uv_dir.y / -uv_dir.x) : uv_dir.x) * 0.05;
    float noise = textureLod(texture_random, vec2(radian, 0.0), 0.0).x * 0.2 + 0.8;
    vec3 light_shaft_color = vec3(0.0);

    float delta_length_ratio = 1.0;

    if(abs(light_shaft_uv.y) < abs(light_shaft_uv.x))
    {
        if(1.0 < light_shaft_uv.x)
        {
            delta_length_ratio = (1.0 - uv.x) / uv_dir.x;
        }
        else if(light_shaft_uv.x < 0.0)
        {
            delta_length_ratio = uv.x / -uv_dir.x;
        }
    }
    else
    {
        if(1.0 < light_shaft_uv.y)
        {
            delta_length_ratio = (1.0 - uv.y) / uv_dir.y;
        }
        else if(light_shaft_uv.y < 0.0)
        {
            delta_length_ratio = uv.y / -uv_dir.y;
        }
    }

    const int sample_count = 30;
    float uv_dist = length(uv_dir);
    uv_dir = normalize(uv_dir);

    float delta_uv_length = uv_dist * delta_length_ratio / float(sample_count);
    vec2 uv_dir_delta = uv_dir * delta_uv_length;
    vec2 sample_uv = uv;


    float ratio = 0.0;

    for(int i=0; i<sample_count; ++i)
    {
        if(sample_uv.x < 0.0 || 1.0 < sample_uv.x || sample_uv.y < 0.0 || 1.0 < sample_uv.y )
        {
            break;
        }

        vec3 diffuse = textureLod(texture_diffuse, sample_uv, 0.0).xyz;
        float luminance = get_luminance(diffuse);
        diffuse *= saturate((0.0 < luminance) ? ((luminance - light_shaft_threshold) / luminance) : 0.0);
        ratio = 1.0 - saturate((uv_dist - delta_uv_length * float(i)) / light_shaft_length);
        light_shaft_color += diffuse * ratio * ratio;
        sample_uv += uv_dir_delta;
    }
    light_shaft_color = light_shaft_color / float(sample_count) * light_shaft_intensity;
    light_shaft_color *= saturate(dot(screen_center_ray, LIGHT_DIRECTION.xyz));

    // scattering
    const float shadow_depth_bias = 0.0025;
    const int count = 30;
    float march_step = min(NEAR_FAR.y, scene_dist) / float(count);
    float intensity = min(1.0, march_step * 2.0);
    vec3 light_shaft = vec3(0.0);

    for(int i=0; i<count; ++i)
    {
        float march_dist = march_step * float(i + 1);
        vec3 march_pos = CAMERA_POSITION.xyz + eye_direction * march_dist;
        vec4 shadow_uv = SHADOW_MATRIX * vec4(march_pos, 1.0);
        shadow_uv.xyz /= shadow_uv.w;
        shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;

        float shadow_depth = textureLod(texture_shadow, shadow_uv.xy, 0.0).x;

        if(shadow_uv.x < 0.0 || 1.0 < shadow_uv.x ||
            shadow_uv.y < 0.0 || 1.0 < shadow_uv.y ||
            shadow_uv.z < 0.0 || 1.0 < shadow_uv.z ||
            shadow_uv.z <= shadow_depth - shadow_depth_bias)
        {
            light_shaft += light_shaft_color * intensity;
        }
    }

    fs_output.xyz = light_shaft * noise / float(count);
    fs_output.w = 1.0;
}
#endif