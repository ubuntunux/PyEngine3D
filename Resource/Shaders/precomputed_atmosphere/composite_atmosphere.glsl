#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform bool above_the_cloud;
uniform float inscatter_power;
uniform sampler2D texture_atmosphere;
uniform sampler2D texture_inscatter;
uniform sampler2D texture_linear_depth;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec2 texcoord = vs_output.tex_coord.xy;
    float linear_depth = texture2D(texture_linear_depth, texcoord).x;
    vec4 color = texture2DLod(texture_atmosphere, texcoord, 0.0);

    color.w = max(color.w, 0.0);

    float depth_ratio = clamp(linear_depth / NEAR_FAR.y, 0.0, 1.0);

    if(above_the_cloud)
    {
        //color.w = (NEAR_FAR.y <= linear_depth) ? 1.0 : color.w;
        color.w = saturate(max(pow(depth_ratio, 2.0), color.w));
    }
    else
    {
        color.w = saturate(pow(depth_ratio, 2.0));
    }

    // for blending : src_color * one + dst_color * (1.0 - src_alpha)
    //color.w = saturate(max(pow(depth_ratio, 2.0), color.w));
    color.xyz *= color.w;

    // Upscaling Inscatter
    vec2 inv_lod_texel_size = 1.0 / textureSize(texture_linear_depth, 2);
    float fixed_linear_depth = texture2DLod(texture_linear_depth, texcoord, 2.0).x;
    float fixed_depth_diff = abs(linear_depth - fixed_linear_depth);
    vec2 fixed_texcoord = (floor(texcoord / inv_lod_texel_size) + 0.5) * inv_lod_texel_size;
    vec2 fixed_uv = fixed_texcoord;

    vec2 offset[8] = {
        vec2(-inv_lod_texel_size.x, 0.0),
        vec2(inv_lod_texel_size.x, 0.0),
        vec2(0.0, inv_lod_texel_size.y),
        vec2(0.0, -inv_lod_texel_size.y),
        vec2(inv_lod_texel_size.x, inv_lod_texel_size.y),
        vec2(-inv_lod_texel_size.x, inv_lod_texel_size.y),
        vec2(inv_lod_texel_size.x, -inv_lod_texel_size.y),
        vec2(-inv_lod_texel_size.x, -inv_lod_texel_size.y),
    };

    for(int i=0; i<8; ++i)
    {
        float lod_linear_depth = texture2DLod(texture_linear_depth, fixed_texcoord + offset[i], 2.0).x;
        float depth_diff = abs(linear_depth - lod_linear_depth);
        if(depth_diff < fixed_depth_diff)
        {
            fixed_linear_depth = lod_linear_depth;
            fixed_depth_diff = depth_diff;
            fixed_uv = fixed_texcoord + offset[i];
        }
    }

    // add inscatter
    color.xyz += texture2D(texture_inscatter, fixed_uv).xyz * pow(depth_ratio, inscatter_power);

    fs_output = color;
}
#endif // FRAGMENT_SHADER