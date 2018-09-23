#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_linear_depth;
uniform sampler2D texture_shadow;

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec2 uv = vs_output.tex_coord;
    vec3 eye_direction = normalize(depth_to_relative_world(uv, 0.0).xyz);

    vec3 screen_center_ray = -vec3(VIEW_ORIGIN[0].z, VIEW_ORIGIN[1].z, VIEW_ORIGIN[2].z);
    float scene_linear_depth = textureLod(texture_linear_depth, uv, 0.0).x;
    float scene_dist = clamp(scene_linear_depth / dot(screen_center_ray, eye_direction), 0.0, NEAR_FAR.y);

    vec3 light_shaft = vec3(0.0);
    vec3 light_shaft_color = LIGHT_COLOR.xyz;
    light_shaft_color *= clamp(dot(eye_direction, LIGHT_DIRECTION.xyz), 0.0, 1.0);

    const float shadow_depth_bias = 0.0025;
    const int count = 128;
    float march_step = min(NEAR_FAR.y, scene_dist) / float(count);
    float intensity = min(1.0, march_step * 2.0);

    for(int i=0; i<count; ++i)
    {
        float march_dist = march_step * float(i + 1);
        vec3 march_pos = CAMERA_POSITION.xyz + eye_direction * march_dist;
        vec4 shadow_uv = SHADOW_MATRIX * vec4(march_pos, 1.0);
        shadow_uv.xyz /= shadow_uv.w;
        shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;

        float shadow_depth = texture2D(texture_shadow, shadow_uv.xy, 0.0).x;

        if(shadow_uv.x < 0.0 || 1.0 < shadow_uv.x ||
            shadow_uv.y < 0.0 || 1.0 < shadow_uv.y ||
            shadow_uv.z < 0.0 || 1.0 < shadow_uv.z ||
            shadow_uv.z <= shadow_depth - shadow_depth_bias)
        {
            light_shaft += light_shaft_color * intensity;
        }
    }

    fs_output.xyz = light_shaft / float(count);
    fs_output.w = 1.0;
}
#endif