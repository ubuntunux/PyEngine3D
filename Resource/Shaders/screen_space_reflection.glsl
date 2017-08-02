#version 430 core

#include "utility.glsl"
#include "scene_constants.glsl"
#include "quad.glsl"

uniform sampler2D texture_diffuse;
uniform sampler2D texture_normal;
uniform sampler2D texture_depth;


//----------- FRAGMENT_SHADER ---------------//

#ifdef FRAGMENT_SHADER
in VERTEX_OUTPUT vs_output;
out vec4 fs_output;

void main() {
    fs_output = vec4(1.0);

    vec2 texcoord = vs_output.texcoord.xy;
    float depth = textureLod(texture_depth, vs_output.texcoord.xy, 0.0).x;

    vec4 clip_coord = vec4(vs_output.texcoord.xy * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 relative_pos = inv_view_origin * inv_perspective * clip_coord;
    relative_pos /= relative_pos.w;

    vec3 V = normalize(-relative_pos.xyz);
    vec3 N = normalize(texture(texture_normal, vs_output.texcoord.xy).xyz);
    vec3 R = normalize(reflect(-V, N));

    int step = 8;
    float marchDist = 0.1;
    for(int i=0; i<step; ++i)
    {
        relative_pos.xyz += R * marchDist;
        clip_coord = perspective * view_origin * vec4(relative_pos.xyz, 1.0);
        clip_coord.xyz /= clip_coord.w;

        texcoord = clip_coord.xy * 0.5 + 0.5;
        float sample_depth = clip_coord.z * 0.5 + 0.5;
        float curr_depth = textureLod(texture_depth, texcoord, 0.0).x;
        if(depth < curr_depth && sample_depth > curr_depth && texcoord.x > 0.0 && texcoord.x < 1.0 && texcoord.y > 0.0 && texcoord.y < 1.0)
         {
            fs_output = texture(texture_diffuse, texcoord.xy);
            fs_output.a = 1.0;
            break;
         }
    }

}
#endif // FRAGMENT_SHADER