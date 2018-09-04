


void main()
{
    vec3 light_shaft = vec3(0.0);
    vec3 light_shaft_color = view_point_sun_irradiance * LIGHT_COLOR.xyz;

    const float shadow_depth_bias = 0.0025;
    const int count = 128;
    float march_step = min(NEAR_FAR.y, scene_dist) / float(count);
    float c = min(1.0, march_step * 10.0);

    for(int i=0; i<count; ++i)
    {
        float march_dist = march_step * float(i + 1);
        vec3 march_pos = CAMERA_POSITION.xyz + eye_direction * march_dist;
        vec4 shadow_uv = SHADOW_MATRIX * vec4(march_pos, 1.0);
        shadow_uv.xyz /= shadow_uv.w;
        shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;

        float shadow_depth = texture2D(texture_shadow, shadow_uv.xy, 0).x;

        if(shadow_uv.x < 0.0 || 1.0 < shadow_uv.x ||
            shadow_uv.y < 0.0 || 1.0 < shadow_uv.y ||
            shadow_uv.z < 0.0 || 1.0 < shadow_uv.z ||
            shadow_uv.z <= shadow_depth - shadow_depth_bias)
        {
            light_shaft += light_shaft_color * c;
        }
    }

    out_lightshaft.xyz = light_shaft / float(count) * 0.0;
    out_lightshaft.w = 1.0;
}