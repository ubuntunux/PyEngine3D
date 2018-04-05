#include "scene_constants.glsl"

float saturate(float value) { return clamp(value, 0.0, 1.0); }
vec2 saturate(vec2 value) { return clamp(value, 0.0, 1.0); }
vec3 saturate(vec3 value) { return clamp(value, 0.0, 1.0); }
vec4 saturate(vec4 value) { return clamp(value, 0.0, 1.0); }

float get_luminance(vec3 color)
{
    return dot(vec3(0.2126, 0.7152, 0.0722), color);
}

float get_linear_luminance(vec3 LinearColor)
{
    return dot(LinearColor, vec3(0.3, 0.59, 0.11));
}

/* non-linear depth to linear depth */
float depth_to_linear_depth(float depth)
{
    const float zNear = NEAR_FAR.x;
    const float zFar = NEAR_FAR.y;
    /* depth [0, 1] to NDC Z [-1, 1] */
    depth = depth * 2.0 - 1.0;
    /* NDC Z to distance[near, far] */
    return 2.0 * zNear * zFar / (zFar + zNear - depth * (zFar - zNear));
}

/* linear depth to non-linear depth */
float linear_depth_to_depth(float linear_depth)
{
    const float zNear = NEAR_FAR.x;
    const float zFar = NEAR_FAR.y;
    /* linear_depth to NDC Z [-1, 1] */
    float depth = (zFar + zNear - 2.0 * zNear * zFar / linear_depth) / (zFar - zNear);
    /* NDC Z [-1, 1] to depth [0, 1] */
    return depth * 0.5 + 0.5;
}

vec4 depth_to_relative_world(vec2 tex_coord, float depth)
{
    vec4 clip_coord = vec4(tex_coord * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 relative_pos = INV_VIEW_ORIGIN * INV_PROJECTION * clip_coord;
    relative_pos /= relative_pos.w;
    return relative_pos;
}

vec4 linear_depth_to_relative_world(vec2 tex_coord, float linear_depth)
{
    // way 1
    float depth = linear_depth_to_depth(linear_depth);

    // way 2 - Note : The camera at the origin is looking along -Z axis in eye space. Therefore, we should use -linear_depth for Z.
    //vec4 ndc = PROJECTION * vec4(0.0, 0.0, -linear_depth, 1.0);
    //float depth = ndc.z / ndc.w;

    return depth_to_relative_world(tex_coord, depth);
}

// @param xy should be a integer position (e.g. pixel position on the screen), repeats each 128x128 pixels
// similar to a texture lookup but is only ALU
// ~13 ALU operations (3 frac, 6 *, 4 mad)
float PseudoRandom(vec2 xy)
{
    vec2 pos = fract(xy / 128.0f) * 128.0f + vec2(-64.340622f, -72.465622f);

    // found by experimentation
    return fract(dot(pos.xyx * pos.xyy, vec3(20.390625f, 60.703125f, 2.4281209f)));
}

float rand(vec2 co){
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

float rand3(vec3 uvw, float scale)
{
	return fract(sin(dot(uvw, vec3(12.9898, 78.233, 45.164))) * 43758.5453123);
}

float rand4(vec4 seed4){
    return fract(sin(dot(seed4, vec4(12.9898, 78.233, 45.164, 94.673))) * 43758.5453123);
}

vec3 invert_y(vec3 vector)
{
    return vec3(vector.x, -vector.y, vector.z);
}

float safe_atan(float y, float x)
{
    return mod(atan(y, x), TWO_PI);
}
