layout(std140, binding=0) uniform sceneConstants
{
    float TIME;
    float JITTER_FRAME;
    float RENDER_SSR;
    float RENDER_SSAO;
    vec2 BACKBUFFER_SIZE;
    vec2 MOUSE_POS;
    vec3 SCENECONSTANTS_DUMMY_0;
    float DELTA_TIME;
};

layout(std140, binding=1) uniform viewConstants
{
    mat4 VIEW;
    mat4 INV_VIEW;
    mat4 VIEW_ORIGIN;
    mat4 INV_VIEW_ORIGIN;
    mat4 PROJECTION;
    mat4 INV_PROJECTION;
    vec4 CAMERA_POSITION;
    vec2 NEAR_FAR;
    vec2 JITTER_DELTA;
    vec2 JITTER_OFFSET;
    vec2 VIEWCONSTANTS_DUMMY0;
};

layout(std140, binding=2) uniform viewProjection
{
    mat4 VIEW_PROJECTION;
    mat4 PREV_VIEW_PROJECTION;
};

layout(std140, binding=3) uniform lightConstants
{
    vec4 LIGHT_POSITION;
    vec4 LIGHT_DIRECTION;
    vec4 LIGHT_COLOR;
    mat4 SHADOW_MATRIX;
};

const int MAX_POINT_LIGHTS = 10;

struct POINT_LIGHT
{
    vec3 color;
    float radius;
    vec3 pos;
    float render;
};

layout(std140, binding=4) uniform pointLightConstants
{
    POINT_LIGHT POINT_LIGHTS[MAX_POINT_LIGHTS];
};

layout(std140, binding=5) uniform emitter_infos
{
    vec2 emitter_delay;
    vec2 emitter_life_time;
    vec3 emitter_velocity_min;
    float emitter_gravity;
    vec3 emitter_velocity_max;
    float emitter_opacity;
    vec3 emitter_position_min;
    float emitter_dummy_0;
    vec3 emitter_position_max;
    float emitter_dummy_1;
};

struct EmitterData
{
    float delay;
    float life_time;
    float gravity;
    float opacity;
    vec3 velocity;
    int alive;
    vec3 position;
    float dummy_0;
};

// referene : RenderOptions.py
#define BLEND 0
#define ADDITIVE 1
#define MULTIPLY 2
#define SUBTRACT 3


const int MAX_BONES_PER_VERTEX = 4;
const int MAX_BONES = 100;
const float SHADOW_BIAS = -0.0001;

const float PI = 3.14159265358979323846;
const float HALF_PI = PI * 0.5;
const float TWO_PI = PI * 2.0;
const float deg = PI / 180.0;

const vec3 kSphereCenter = vec3(1.0, 1.0, -2.0);
const float kSphereRadius = 1.0;
const vec3 kSphereAlbedo = vec3(0.8);
const vec3 kGroundAlbedo = vec3(0.0, 0.0, 0.04);



