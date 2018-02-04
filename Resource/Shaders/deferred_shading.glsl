#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "quad.glsl"
#include "precomputed_atmosphere/atmosphere_predefine.glsl"


uniform sampler2D texture_diffuse;
uniform sampler2D texture_material;
uniform sampler2D texture_normal;

uniform sampler2D texture_depth;
uniform sampler2D texture_shadow;
uniform sampler2D texture_ssao;
uniform sampler2D texture_scene_reflect;
uniform samplerCube texture_probe;


// Atmosphere
uniform vec3 earth_center;
uniform vec2 sun_size;
uniform float exposure;

uniform sampler2D texture_linear_depth;
uniform sampler2D transmittance_texture;
uniform sampler3D scattering_texture;
uniform sampler3D single_mie_scattering_texture;
uniform sampler2D irradiance_texture;

uniform vec3 SKY_RADIANCE_TO_LUMINANCE;
uniform vec3 SUN_RADIANCE_TO_LUMINANCE;


vec3 GetSolarRadiance()
{
    return ATMOSPHERE.solar_irradiance /
        (PI * ATMOSPHERE.sun_angular_radius * ATMOSPHERE.sun_angular_radius) *
        SUN_RADIANCE_TO_LUMINANCE;
}

vec3 GetSkyRadiance(
    vec3 camera, vec3 view_ray, float shadow_length,
    vec3 sun_direction, out vec3 transmittance)
{
    return ComputeSkyRadiance(ATMOSPHERE, transmittance_texture,
        scattering_texture, single_mie_scattering_texture,
        camera, view_ray, shadow_length, sun_direction, transmittance) *
        SKY_RADIANCE_TO_LUMINANCE;
}

vec3 GetSkyRadianceToPoint(
    vec3 camera, vec3 point, float shadow_length,
    vec3 sun_direction, out vec3 transmittance)
{
    return ComputeSkyRadianceToPoint(ATMOSPHERE, transmittance_texture,
        scattering_texture, single_mie_scattering_texture,
        camera, point, shadow_length, sun_direction, transmittance) *
        SKY_RADIANCE_TO_LUMINANCE;
}

vec3 GetSunAndSkyIrradiance(
   vec3 p, vec3 normal, vec3 sun_direction,
   out vec3 sky_irradiance)
{
    vec3 sun_irradiance = ComputeSunAndSkyIrradiance(
        ATMOSPHERE, transmittance_texture, irradiance_texture, p, normal,
        sun_direction, sky_irradiance);
    sky_irradiance *= SKY_RADIANCE_TO_LUMINANCE;
    return sun_irradiance * SUN_RADIANCE_TO_LUMINANCE;
}

float GetSunVisibility(vec3 point, vec3 sun_direction)
{
    vec3 p = point - kSphereCenter;
    float p_dot_v = dot(p, sun_direction);
    float p_dot_p = dot(p, p);
    float ray_sphere_center_squared_distance = p_dot_p - p_dot_v * p_dot_v;
    float distance_to_intersection = -p_dot_v - sqrt(
        kSphereRadius * kSphereRadius - ray_sphere_center_squared_distance);
    if (distance_to_intersection > 0.0)
    {
        float ray_sphere_distance = kSphereRadius - sqrt(ray_sphere_center_squared_distance);
        float ray_sphere_angular_distance = -ray_sphere_distance / p_dot_v;
        return smoothstep(1.0, 0.0, ray_sphere_angular_distance / sun_size.x);
    }
    return 1.0;
}

float GetSkyVisibility(vec3 point)
{
  vec3 p = point - kSphereCenter;
  float p_dot_p = dot(p, p);
  return 1.0 + p.y / sqrt(p_dot_p) * kSphereRadius * kSphereRadius / p_dot_p;
}

void GetSphereShadowInOut(vec3 view_direction, vec3 sun_direction, out float d_in, out float d_out)
{
    vec3 pos = CAMERA_POSITION.xyz - kSphereCenter;
    float pos_dot_sun = dot(pos, sun_direction);
    float view_dot_sun = dot(view_direction, sun_direction);
    float k = sun_size.x;
    float l = 1.0 + k * k;
    float a = 1.0 - l * view_dot_sun * view_dot_sun;
    float b = dot(pos, view_direction) - l * pos_dot_sun * view_dot_sun - k * kSphereRadius * view_dot_sun;
    float c = dot(pos, pos) - l * pos_dot_sun * pos_dot_sun -
        2.0 * k * kSphereRadius * pos_dot_sun - kSphereRadius * kSphereRadius;
    float discriminant = b * b - a * c;
    if (discriminant > 0.0)
    {
        d_in = max(0.0, (-b - sqrt(discriminant)) / a);
        d_out = (-b + sqrt(discriminant)) / a;
        float d_base = -pos_dot_sun / view_dot_sun;
        float d_apex = -(pos_dot_sun + kSphereRadius / k) / view_dot_sun;
        if (view_dot_sun > 0.0)
        {
            d_in = max(d_in, d_apex);
            d_out = a > 0.0 ? min(d_out, d_base) : d_base;
        }
        else
        {
            d_in = a > 0.0 ? max(d_in, d_base) : d_base;
            d_out = min(d_out, d_apex);
        }
    }
    else
    {
        d_in = 0.0;
        d_out = 0.0;
    }
}


#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 screen_tex_coord = vs_output.tex_coord.xy;

    float depth = texture(texture_depth, screen_tex_coord).x;

    if(depth == 1.0)
    {
        discard;
    }

    vec4 base_color = texture(texture_diffuse, screen_tex_coord);
    // decoding
    base_color.w *= 10.0;

    vec4 material = texture(texture_material, screen_tex_coord);
    vec3 N = normalize(texture(texture_normal, screen_tex_coord).xyz * 2.0 - 1.0);

    vec4 world_position = vec4(screen_tex_coord * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    world_position = INV_VIEW * INV_PROJECTION * world_position;
    world_position /= world_position.w;

    float roughness = material.x;
    float metalicness = material.y;
    float reflectance = material.z;

    vec3 V = normalize(CAMERA_POSITION.xyz - world_position.xyz);
    vec3 L = normalize(LIGHT_DIRECTION.xyz);

    float shadow_factor = get_shadow_factor(screen_tex_coord, world_position.xyz, texture_shadow);

    // Atmosphere
    vec3 radiance = vec3(0.0);
    {
        vec3 camera = CAMERA_POSITION.xyz;
        vec3 sun_direction = LIGHT_DIRECTION.xyz;

        vec3 view_direction = normalize(-V);
        float scene_linear_depth = texture(texture_linear_depth, screen_tex_coord).x;
        vec3 scene_point = view_direction * scene_linear_depth;

        float lightshaft_fadein_hack = smoothstep(0.02, 0.04, dot(normalize(camera - earth_center), sun_direction));

        float earth_radius = abs(earth_center.y);
        float ratio = 0.1;

        vec3 p;
        float p_dot_v;
        float p_dot_p;
        float squared_radius;
        float sphere_shadow_in = 0.0;
        float sphere_shadow_out = 0.0;

        // Scene
        float scene_shadow_length = 0.0;
        vec3 scene_radiance = vec3(0.0);
        {
            vec3 normal = normalize(texture(texture_normal, screen_tex_coord).xyz * 2.0 - 1.0);
            vec3 point = (camera + scene_point) * ratio;

            bool shadow_enter = false;
            bool do_exit = false;
            float scene_shadow_out = 0.0;
            float scene_shadow_in = 0.0;
            float d = 0.2;
            vec3 normalized_dir = normalize(scene_point);

            const int LOOP = 100;
            for(int i=0; i<LOOP; ++i)
            {
                float ray_dist = float(i) * d;
                vec3 world_pos = camera + normalized_dir * ray_dist;
                vec4 shadow_uv = SHADOW_MATRIX * vec4(world_pos, 1.0);
                shadow_uv.xyz /= shadow_uv.w;
                shadow_uv.xyz = shadow_uv.xyz * 0.5 + 0.5;
                float shadow_depth = texture(texture_shadow, shadow_uv.xy, 0).x;

                if(shadow_uv.x < 0.0 || 1.0 < shadow_uv.x || shadow_uv.y < 0.0 || 1.0 < shadow_uv.y)
                {
                    do_exit = true;
                }
                else if(false == shadow_enter && shadow_depth <= shadow_uv.z)
                {
                    // enter the shadow.
                    shadow_enter = true;
                    scene_shadow_in = dot(normalized_dir, world_pos);

                    if(length(world_pos - earth_center) < earth_radius)
                    {
                        // Clip shdoaw by ground. Check if the ray enters the earth.
                        do_exit = true;
                    }
                }
                else if(shadow_enter && (shadow_uv.z < shadow_depth || scene_linear_depth <= ray_dist))
                {
                    // It came out of the shadows or hit the surface of the object.
                    do_exit = true;
                }

                if(do_exit || i == (LOOP-1))
                {
                    if(shadow_enter)
                    {
                        // If there is already a shadow, set the position outside the shadow to the current position.
                        scene_shadow_out = dot(normalized_dir, world_pos);
                    }
                    else
                    {
                        // Shadow not detected.
                        scene_shadow_in = 0.0;
                        scene_shadow_out = 0.0;
                    }
                    break;
                }
            }

            scene_shadow_length = max(0.0, scene_shadow_out - scene_shadow_in);

            vec3 sky_irradiance;
            vec3 sun_irradiance = GetSunAndSkyIrradiance( point.xyz - earth_center, normal, sun_direction, sky_irradiance);
            scene_radiance = kSphereAlbedo * (1.0 / PI) * (sun_irradiance + sky_irradiance);

            vec3 transmittance;
            vec3 in_scatter = GetSkyRadianceToPoint(camera - earth_center, point.xyz - earth_center, scene_shadow_length, sun_direction, transmittance);
            scene_radiance = scene_radiance * transmittance + in_scatter;
        }

        // Sky
        float shadow_length = max(scene_shadow_length, max(0.0, sphere_shadow_out - sphere_shadow_in)) * lightshaft_fadein_hack;

        vec3 transmittance;
        vec3 radiance = GetSkyRadiance(camera * ratio - earth_center, view_direction, shadow_length, sun_direction, transmittance);

        // Sun
        if (dot(view_direction, sun_direction) > sun_size.y)
        {
            radiance = radiance + transmittance * GetSolarRadiance();
        }

        // Final composite
        radiance = mix(scene_radiance, radiance, scene_linear_depth < NEAR_FAR.y ? 0.0 : 1.0);
    }

    fs_output = surface_shading(base_color,
                    metalicness,
                    roughness,
                    reflectance,
                    texture_probe,
                    texture_scene_reflect,
                    screen_tex_coord,
                    LIGHT_COLOR.xyz * radiance * exposure,
                    N,
                    V,
                    L,
                    shadow_factor);

    // SSAO
    if(RENDER_SSAO == 1.0f)
    {
        fs_output.xyz *= texture(texture_ssao, screen_tex_coord).x;
    }

    // emissive
    fs_output.xyz += base_color.xyz * base_color.w;
    fs_output.w = 1.0;
}
#endif