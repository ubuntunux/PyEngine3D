#include "scene_constants.glsl"

vec4 depth_to_relative_world_pos(vec2 tex_coord, float depth)
{
    vec4 clip_coord = vec4(tex_coord * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 relative_pos = inv_perspective * clip_coord;
    relative_pos /= relative_pos.w;
    return inv_view * relative_pos;
}


vec4 world_pos_to_clip_space(vec3 world_pos)
{
    // clip space [-1, -1, -1] ~ [1, 1, 1]
    vec4 clip_coord = perspective * view * vec4(world_pos, 1.0);
    return clip_coord / clip_coord.w;
}

// non-linear depth to non-linear depth
float depth_to_distance(float zNear, float zFar, float depth)
{
    // depth [0, 1] to NDC Z [-1, 1]
    depth = depth * 2.0 - 1.0;
    // NDC Z to distance[near, far]
    return 2.0 * zNear * zFar / (zFar + zNear - depth * (zFar - zNear));
}

// linear depth to non-linear depth
float distance_to_depth(float zNear, float zFar, float distance)
{
    // distance to NDC Z [-1, 1]
    float depth = (zFar + zNear - 2.0 * zNear * zFar / distance) / (zFar - zNear);
    // NDC Z [-1, 1] to depth [0, 1]
    return depth * 0.5 + 0.5;
}

float rand(vec2 co){
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

float rand2(vec4 seed4){
    float dot_product = dot(seed4, vec4(12.9898,78.233,45.164,94.673));
    return fract(sin(dot_product) * 43758.5453);
}

vec3 invert_y(vec3 vector)
{
    return vec3(vector.x, -vector.y, vector.z);
}