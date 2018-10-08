#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_material;
uniform sampler2D texture_normal;

uniform sampler2D texture_depth;
uniform sampler2D texture_shadow;
uniform sampler2D texture_ssao;
uniform sampler2D texture_scene_reflect;
uniform samplerCube texture_probe;


#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main() {
    vec2 screen_tex_coord = vs_output.tex_coord.xy;

    float depth = texture2D(texture_depth, screen_tex_coord).x;

    if(depth == 1.0)
    {
        fs_output = vec4(0.0);
        return;
    }

    vec4 base_color = texture2D(texture_diffuse, screen_tex_coord);
    // decoding
    base_color.w *= 10.0;

    vec4 material = texture2D(texture_material, screen_tex_coord);
    vec3 N = normalize(texture2D(texture_normal, screen_tex_coord).xyz * 2.0 - 1.0);

    vec4 world_position = vec4(screen_tex_coord * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    world_position = INV_VIEW * INV_PROJECTION * world_position;
    world_position /= world_position.w;

    float roughness = material.x;
    float metalicness = material.y;
    float reflectance = material.z;

    vec3 V = normalize(CAMERA_POSITION.xyz - world_position.xyz);
    vec3 L = normalize(LIGHT_DIRECTION.xyz);

    fs_output = surface_shading(
                    base_color,
                    base_color.xyz * base_color.w,
                    metalicness,
                    roughness,
                    reflectance,
                    texture2D(texture_ssao, screen_tex_coord).x,
                    texture2D(texture_scene_reflect, screen_tex_coord),
                    texture_probe,
                    texture_shadow,
                    screen_tex_coord,
                    world_position.xyz,
                    LIGHT_COLOR.xyz,
                    N,
                    V,
                    L,
                    depth);

    fs_output.w = 1.0;
}
#endif