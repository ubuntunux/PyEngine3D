#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

const int GL_TEXTURE_2D = 3553;
const int GL_TEXTURE_2D_ARRAY = 35866;
const int GL_TEXTURE_3D = 32879;
const int GL_TEXTURE_CUBE_MAP = 34067;

uniform sampler2D texture_source_2d;
uniform sampler2DArray texture_source_2d_array;
uniform sampler3D texture_source_3d;
uniform samplerCube texture_source_cube;

uniform bool debug_absolute;
uniform float debug_mipmap;
uniform float debug_intensity_min;
uniform float debug_intensity_max;
uniform int debug_target;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

vec4 get_texture_2d_array(sampler2DArray texture_source)
{
    vec3 texture_size = textureSize(texture_source, 0);
    float width = ceil(sqrt(texture_size.z));
    float height = ceil(texture_size.z / width);
    float depth = floor(vs_output.tex_coord.x * width) + floor((1.0 - vs_output.tex_coord.y) * height) * width;
    if(texture_size.z <= depth)
    {
        return vec4(0.0, 0.0, 0.0, 0.0);
    }
    vec3 texcoord = vec3(fract(vs_output.tex_coord.x * width), fract(vs_output.tex_coord.y * height), depth);
    return texture2DArray(texture_source, texcoord, debug_mipmap);
}

vec4 get_texture_3d(sampler3D texture_source)
{
    vec3 texture_size = textureSize(texture_source, 0);
    float width = ceil(sqrt(texture_size.z));
    float height = ceil(texture_size.z / width);
    float depth = floor(vs_output.tex_coord.x * width) + floor((1.0 - vs_output.tex_coord.y) * height) * width;
    if(texture_size.z <= depth)
    {
        return vec4(0.0, 0.0, 0.0, 0.0);
    }
    depth /= texture_size.z;
    vec3 texcoord = vec3(fract(vs_output.tex_coord.x * width), fract(vs_output.tex_coord.y * height), depth);
    return texture3D(texture_source, texcoord, debug_mipmap);
}

void main()
{
    if(GL_TEXTURE_2D == debug_target)
    {
        vec2 texcoord = vs_output.tex_coord.xy;
        fs_output = texture2D(texture_source_2d, texcoord, debug_mipmap);
    }
    else if(GL_TEXTURE_2D_ARRAY == debug_target)
    {
        fs_output = get_texture_2d_array(texture_source_2d_array);
    }
    else if(GL_TEXTURE_3D == debug_target)
    {
        fs_output = get_texture_3d(texture_source_3d);
    }
    else if(GL_TEXTURE_CUBE_MAP == debug_target)
    {
        vec4 position = vec4(vs_output.tex_coord.xy * 2.0 - 1.0 + JITTER_OFFSET, -1.0, 1.0);
        position = INV_VIEW_ORIGIN * INV_PROJECTION * position;
        position.xyz /= position.w;
        position.y = -position.y;
        fs_output = textureCube(texture_source_cube, normalize(position.xyz), debug_mipmap);
    }

    if(debug_absolute)
    {
        fs_output.xyz = abs(fs_output.xyz);
    }

    fs_output.xyz = clamp((fs_output.xyz - debug_intensity_min) / (debug_intensity_max - debug_intensity_min), 0.0, 1.0);
    fs_output.w = 1.0;
}
#endif // FRAGMENT_SHADER