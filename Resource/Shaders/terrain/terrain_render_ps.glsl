#include "terrain/terrain_render_vs.glsl"

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;

layout (location = 0) out vec4 fs_diffuse;
layout (location = 1) out vec4 fs_material;
layout (location = 2) out vec4 fs_normal;

void main()
{
    float emissive = 0.0;
    float roughness = 1.0;
    float metalicness = 0.0;
    float reflectance = 0.0;
    vec3 normal = normalize(vs_output.vertex_normal.xyz);

    fs_diffuse.xyz = pow(texture2D(texture_height_map, vs_output.tex_coord).xyz, vec3(2.2));
    fs_diffuse.w = emissive;

    fs_material = vec4(roughness, metalicness, reflectance, 0.0);
    fs_normal = vec4(normal * 0.5 + 0.5, 0.0);
}
#endif
