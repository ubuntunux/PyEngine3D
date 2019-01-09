#include "scene_constants.glsl"

const int FilterTypes_Box = 0;
const int FilterTypes_Triangle = 1;
const int FilterTypes_Gaussian = 2;
const int FilterTypes_BlackmanHarris = 3;
const int FilterTypes_Smoothstep = 4;
const int FilterTypes_BSpline = 5;
const int FilterTypes_CatmullRom = 6;
const int FilterTypes_Mitchell = 7;
const int FilterTypes_GeneralizedCubic = 8;
const int FilterTypes_Sinc = 9;


float FilterBox(in float x)
{
    return x <= 1.0 ? 1.0 : 0.0;
}

float FilterTriangle(in float x)
{
    return clamp(1.0f - x, 0.0, 1.0);
}

float FilterGaussian(in float x)
{
    const float sigma = 0.25;
    const float g = 1.0f / sqrt(2.0f * 3.14159f * sigma * sigma);
    return (g * exp(-(x * x) / (2 * sigma * sigma)));
}

float FilterCubic(in float x, in float B, in float C)
{
    float y = 0.0f;
    float x2 = x * x;
    float x3 = x * x * x;

    if(x < 1)
    {
        y = (12 - 9 * B - 6 * C) * x3 + (-18 + 12 * B + 6 * C) * x2 + (6 - 2 * B);
    }
    else if(x <= 2)
    {
        y = (-B - 6 * C) * x3 + (6 * B + 30 * C) * x2 + (-12 * B - 48 * C) * x + (8 * B + 24 * C);
    }

    return y / 6.0f;
}

float FilterSinc(in float x, in float filterRadius)
{
    float s;
    x *= filterRadius * 2.0f;
    if(x < 0.001f)
        s = 1.0f;
    else
        s = sin(x * PI) / (x * PI);
    return s;
}

float FilterBlackmanHarris(in float x)
{
    x = 1.0f - x;
    const float a0 = 0.35875f;
    const float a1 = 0.48829f;
    const float a2 = 0.14128f;
    const float a3 = 0.01168f;
    return clamp(a0 - a1 * cos(PI * x) + a2 * cos(2 * PI * x) - a3 * cos(3 * PI * x), 0.0, 1.0);
}

float FilterSmoothstep(in float x)
{
    return 1.0f - smoothstep(0.0f, 1.0f, x);
}

float Filter(in float x, in int filterType, in float filterRadius, in bool rescaleCubic)
{
    // Cubic filters naturually work in a [-2, 2] domain. For the resolve case we
    // want to rescale the filter so that it works in [-1, 1] instead
    float cubicX = rescaleCubic ? x * 2.0f : x;

    if(filterType == FilterTypes_Box)
        return FilterBox(x);
    else if(filterType == FilterTypes_Triangle)
        return FilterTriangle(x);
    else if(filterType == FilterTypes_Gaussian)
        return FilterGaussian(x);
    else if(filterType == FilterTypes_BlackmanHarris)
        return FilterBlackmanHarris(x);
    else if(filterType == FilterTypes_Smoothstep)
        return FilterSmoothstep(x);
    else if(filterType == FilterTypes_BSpline)
        return FilterCubic(cubicX, 1.0, 0.0f);
    else if(filterType == FilterTypes_CatmullRom)
        return FilterCubic(cubicX, 0, 0.5f);
    else if(filterType == FilterTypes_Mitchell)
        return FilterCubic(cubicX, 1 / 3.0f, 1 / 3.0f);
    else if(filterType == FilterTypes_GeneralizedCubic)
        return FilterCubic(cubicX, 0.33, 0.33);
    else if(filterType == FilterTypes_Sinc)
        return FilterSinc(x, filterRadius);
    else
        return 1.0f;
}

float saturate(float value) { return clamp(value, 0.0, 1.0); }
vec2 saturate(vec2 value) { return clamp(value, 0.0, 1.0); }
vec3 saturate(vec3 value) { return clamp(value, 0.0, 1.0); }
vec4 saturate(vec4 value) { return clamp(value, 0.0, 1.0); }

float get_luminance(vec3 color)
{
    return dot(vec3(0.2126, 0.7152, 0.0722), color);
}

// depth(0.0 ~ 1.0) to linear depth(near ~ far)
float depth_to_linear_depth(float depth)
{
    const float zNear = NEAR_FAR.x;
    const float zFar = NEAR_FAR.y;
    // depth [0, 1] to NDC Z [-1, 1]
    depth = depth * 2.0 - 1.0;
    // NDC Z to distance[near, far]
    return 2.0 * zNear * zFar / (zFar + zNear - depth * (zFar - zNear));
}

// linear depth(near ~ far) to non-linear depth(0.0 ~ 1.0)
float linear_depth_to_depth(float linear_depth)
{
    const float zNear = NEAR_FAR.x;
    const float zFar = NEAR_FAR.y;
    // linear_depth to NDC Z [-1, 1]
    float depth = (zFar + zNear - 2.0 * zNear * zFar / linear_depth) / (zFar - zNear);
    // NDC Z [-1, 1] to depth [0, 1]
    return depth * 0.5 + 0.5;
}

vec4 linear_depth_to_depth(vec4 linear_depth)
{
    const vec4 zNear = NEAR_FAR.xxxx;
    const vec4 zFar = NEAR_FAR.yyyy;
    vec4 depth = (zFar + zNear - 2.0 * zNear * zFar / linear_depth) / (zFar - zNear);
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


// Random Generate Interface
vec4 generate_random(float random_seed)
{
    vec4 random_factor;
    float time = fract(TIME * 0.001);
    random_factor.x = rand(vec2(time, random_seed));
    random_factor.y = rand(vec2(random_factor.x, time));
    random_factor.z = rand(vec2(time, random_factor.y));
    random_factor.w = rand(vec2(random_factor.z, time));
    return random_factor;
}

void generate_random1(inout vec4 random_factor)
{
    float time = fract(TIME * 0.001);
    random_factor.x = rand(vec2(time, random_factor.w));
    random_factor.w = random_factor.x;
}

void generate_random2(inout vec4 random_factor)
{
    float time = fract(TIME * 0.001);
    random_factor.x = rand(vec2(time, random_factor.w));
    random_factor.y = rand(vec2(random_factor.x, time));
    random_factor.w = random_factor.y;
}

void generate_random3(inout vec4 random_factor)
{
    float time = fract(TIME * 0.001);
    random_factor.x = rand(vec2(time, random_factor.w));
    random_factor.y = rand(vec2(random_factor.x, time));
    random_factor.z = rand(vec2(time, random_factor.y));
    random_factor.w = random_factor.z;
}

void generate_random4(inout vec4 random_factor)
{
    float time = fract(TIME * 0.001);
    random_factor.x = rand(vec2(time, random_factor.w));
    random_factor.y = rand(vec2(random_factor.x, time));
    random_factor.z = rand(vec2(time, random_factor.y));
    random_factor.w = rand(vec2(random_factor.z, time));
}


vec3 invert_y(vec3 vector)
{
    return vec3(vector.x, -vector.y, vector.z);
}

float safe_atan(float y, float x)
{
    return mod(atan(y, x), TWO_PI);
}

vec2 safe_normalize(vec2 vector)
{
    float dist = length(vector);
    return vector / (dist == 0.0 ? 1.0 : dist);
}

vec3 safe_normalize(vec3 vector)
{
    float dist = length(vector);
    return vector / (dist == 0.0 ? 1.0 : dist);
}

vec4 safe_normalize(vec4 vector)
{
    float dist = length(vector);
    return vector / (dist == 0.0 ? 1.0 : dist);
}