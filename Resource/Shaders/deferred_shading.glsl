

#include "scene_constants.glsl"
#include "utility.glsl"
#include "shading.glsl"
#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_material;
uniform sampler2D texture_normal;

uniform sampler2D texture_depth;
uniform sampler2D texture_shadow;
uniform sampler2D texture_scene_reflect;
uniform samplerCube texture_cube;

#ifdef FRAGMENT_SHADER
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
    world_position = INV_VIEW * INV_PERSPECTIVE * world_position;
    world_position /= world_position.w;

    float roughness = material.x;
    float metalicness = material.y;
    float reflectance = material.z;

    vec3 V = normalize(CAMERA_POSITION.xyz - world_position.xyz);
    vec3 L = normalize(LIGHT_DIRECTION.xyz);

    float shadow_factor = get_shadow_factor(screen_tex_coord, world_position.xyz, texture_shadow);

    fs_output = surface_shading(base_color,
                    metalicness,
                    roughness,
                    reflectance,
                    texture_cube,
                    texture_scene_reflect,
                    screen_tex_coord,
                    LIGHT_COLOR.xyz,
                    N,
                    V,
                    L,
                    shadow_factor);

    fs_output.xyz += base_color.xyz * base_color.w;
    fs_output.w = 1.0;
}
#endif