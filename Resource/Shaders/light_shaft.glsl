#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_random;
uniform sampler2D texture_depth;
uniform float light_shaft_intensity;
uniform float light_shaft_threshold;
uniform float light_shaft_radius;
uniform float light_shaft_decay;
uniform int light_shaft_samples;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec2 uv = vs_output.tex_coord;
    vec3 screen_center_ray = -vec3(VIEW_ORIGIN[0].z, VIEW_ORIGIN[1].z, VIEW_ORIGIN[2].z);

    const float screenRatio = BACKBUFFER_SIZE.y / BACKBUFFER_SIZE.x;

    vec4 sun_proj = PROJECTION * VIEW_ORIGIN * vec4(LIGHT_DIRECTION.xyz * NEAR_FAR.y, 1.0);
    sun_proj.xyz /= sun_proj.w;
    vec2 sun_uv = sun_proj.xy * 0.5 + 0.5;

    vec2 uv_dir = sun_uv - uv;
    float radian = atan((0.0 != uv_dir.x) ? (uv_dir.y / -uv_dir.x) : uv_dir.x) * 0.05;
    float noise = textureLod(texture_random, vec2(radian, 0.0), 0.0).x * 0.2 + 0.8;

    vec2 uv_dir_delta = uv_dir / float(light_shaft_samples);
    float uv_dist = length(vec2(uv_dir.x, uv_dir.y * screenRatio));
    vec2 sample_uv = uv;

    float illuminationDecay = 1.0;
    float ratio = 0.0;
    vec3 light_shaft_color = vec3(0.0);

    for(int i=0; i<light_shaft_samples; ++i)
    {
        if(sample_uv.x < 0.0 || 1.0 < sample_uv.x || sample_uv.y < 0.0 || 1.0 < sample_uv.y )
        {
            break;
        }

        vec2 temp_uv_dir = sample_uv - sun_uv;
        temp_uv_dir.y *= screenRatio;

        if(1.0 <= textureLod(texture_depth, sample_uv, 0.0).x && length(temp_uv_dir) < light_shaft_radius)
        {
            vec3 diffuse = textureLod(texture_diffuse, sample_uv, 0.0).xyz;
            float luminance = get_luminance(diffuse);
            diffuse *= saturate((0.0 < luminance) ? ((luminance - light_shaft_threshold) / luminance) : 0.0);
            light_shaft_color += diffuse * illuminationDecay;
        }

        illuminationDecay *= light_shaft_decay;
        sample_uv += uv_dir_delta;
    }

    light_shaft_color *= saturate(dot(screen_center_ray, LIGHT_DIRECTION.xyz)) / float(light_shaft_samples);
    light_shaft_color *= light_shaft_intensity * noise;

    fs_output.xyz = light_shaft_color;
    fs_output.w = 1.0;
}
#endif