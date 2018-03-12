#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

#define GL_TEXTURE_2D 0
#define GL_TEXTURE_2D_ARRAY 0
#define GL_TEXTURE_3D 0
#define GL_TEXTURE_CUBE_MAP 0

#if GL_TEXTURE_2D == 1
    uniform sampler2D texture_source;
#elif GL_TEXTURE_2D_ARRAY == 1
    uniform sampler2DArray texture_source;
#elif GL_TEXTURE_3D == 1
    uniform sampler3D texture_source;
#elif GL_TEXTURE_CUBE_MAP == 1
    uniform samplerCube texture_source;
#endif

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

vec4 get_texture_3d(sampler3D texture_source)
{
    vec3 texture_size = textureSize(texture_source, 0);
    float l = log2(texture_size.z);
    float width = exp2(ceil(l / 2.0));
    float height = texture_size.z / width;
    float depth = floor(vs_output.tex_coord.x * width) + floor((1.0 - vs_output.tex_coord.y) * height) * width;
    if(texture_size.z < depth)
    {
        depth = 0.0;
    }
    else
    {
        depth /= texture_size.z;
    }
    vec3 texcoord = vec3(fract(vs_output.tex_coord.x * width), fract(vs_output.tex_coord.y * height), depth);
    return texture(texture_source, texcoord);
}

vec4 get_texture_2d_array(sampler2DArray texture_source)
{
    vec3 texture_size = textureSize(texture_source, 0);
    float l = log2(texture_size.z);
    float width = exp2(ceil(l / 2.0));
    float height = texture_size.z / width;
    float depth = floor(vs_output.tex_coord.x * width) + floor((1.0 - vs_output.tex_coord.y) * height) * width;
    if(texture_size.z < depth)
    {
        depth = 0.0;
    }
    vec3 texcoord = vec3(fract(vs_output.tex_coord.x * width), fract(vs_output.tex_coord.y * height), depth);
    return texture(texture_source, texcoord);
}


void main() {
#if GL_TEXTURE_2D == 1
    vec2 texcoord = vs_output.tex_coord.xy;
    fs_output = texture(texture_source, texcoord) * 1000.0;
#elif GL_TEXTURE_2D_ARRAY == 1
    fs_output = get_texture_2d_array(texture_source);
#elif GL_TEXTURE_3D == 1
    fs_output = get_texture_3d(texture_source);
#elif GL_TEXTURE_CUBE_MAP == 1
    vec4 position = vec4(vs_output.tex_coord.xy * 2.0 - 1.0 + JITTER_OFFSET, -1.0, 1.0);
    position = INV_VIEW_ORIGIN * INV_PROJECTION * position;
    position.xyz /= position.w;
    position.y = -position.y;
    fs_output = texture(texture_source, normalize(position.xyz));
#endif

    fs_output.w = 1.0;
}
#endif // GL_FRAGMENT_SHADER