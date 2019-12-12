layout(std140, binding=0) uniform scene_constants
{
    float TIME;
    float JITTER_FRAME;
    bool RENDER_SSR;
    bool RENDER_SSAO;
    vec2 SCREEN_SIZE;
    vec2 BACKBUFFER_SIZE;
    vec2 MOUSE_POS;
    float DELTA_TIME;
    int SCENE_DUMMY_0;
};

layout(std140, binding=1) uniform view_constants
{
    mat4 VIEW;
    mat4 INV_VIEW;
    mat4 VIEW_ORIGIN;
    mat4 INV_VIEW_ORIGIN;
    mat4 PROJECTION;
    mat4 INV_PROJECTION;
    vec3 CAMERA_POSITION;
    float VIEW_DUMMY_0;
    vec2 NEAR_FAR;
    vec2 JITTER_DELTA;
    vec2 JITTER_OFFSET;
    vec2 VIEWCONSTANTS_DUMMY0;
};

layout(std140, binding=2) uniform view_projection
{
    mat4 VIEW_PROJECTION;
    mat4 PREV_VIEW_PROJECTION;
};

layout(std140, binding=3) uniform light_constants
{
    mat4 SHADOW_MATRIX;
    vec3 LIGHT_POSITION;
    float SHADOW_EXP;
    vec3 LIGHT_DIRECTION;
    float SHADOW_BIAS;
    vec3 LIGHT_COLOR;
    int SHADOW_SAMPLES;
};

const int MAX_POINT_LIGHTS = 10;

struct POINT_LIGHT
{
    vec3 color;
    float radius;
    vec3 pos;
    float render;
};

layout(std140, binding=4) uniform point_light_constants
{
    POINT_LIGHT POINT_LIGHTS[MAX_POINT_LIGHTS];
};


layout(std140, binding=5) uniform particle_common
{
    vec3 PARTICLE_COLOR;
    int PARTICLE_ALIGN_MODE;
    ivec2 PARTICLE_CELL_COUNT;
    int PARTICLE_BLEND_MODE;
    int PARTICLE_COMMON_DUMMY_0;
};

layout(std140, binding=6) uniform particle_infos
{
    mat4 PARTICLE_PARENT_MATRIX;
    vec2 PARTICLE_DELAY;
    vec2 PARTICLE_LIFE_TIME;
    vec3 PARTICLE_TRANSFORM_ROTATION_MIN;
    float PARTICLE_FADE_IN;
    vec3 PARTICLE_TRANSFORM_ROTATION_MAX;
    float PARTICLE_FADE_OUT;
    vec3 PARTICLE_TRANSFORM_SCALE_MIN;
    float PARTICLE_OPACITY;
    vec3 PARTICLE_TRANSFORM_SCALE_MAX;
    bool PARTICLE_ENABLE_VECTOR_FIELD;
    vec3 PARTICLE_VELOCITY_POSITION_MIN;
    float PARTICLE_VECTOR_FIELD_STRENGTH;
    vec3 PARTICLE_VELOCITY_POSITION_MAX;
    float PARTICLE_VECTOR_FIELD_TIGHTNESS;
    vec3 PARTICLE_VELOCITY_ROTATION_MIN;
    uint PARTICLE_MAX_COUNT;
    vec3 PARTICLE_VELOCITY_ROTATION_MAX;
    uint PARTICLE_SPAWN_COUNT;
    vec3 PARTICLE_VELOCITY_SCALE_MIN;
    float PARTICLE_VELOCITY_STRETCH;
    vec3 PARTICLE_VELOCITY_SCALE_MAX;
    float PARTICLE_VELOCITY_ACCELERATION;
    mat4 PARTICLE_VECTOR_FIELD_MATRIX;
    mat4 PARTICLE_VECTOR_FIELD_INV_MATRIX;
    vec3 PARTICLE_SPAWN_VOLUME_INFO;
    uint PARTICLE_SPAWN_VOLUME_TYPE;
    mat4 PARTICLE_SPAWN_VOLUME_MATRIX;
    vec2 PARTICLE_VELOCITY_LIMIT;
    float PARTICLE_FORCE_GRAVITY;
    float PARTICLE_PLAY_SPEED;
    uint PARTICLE_VELOCITY_TYPE;
    float PARTICLE_FORCE_ELASTICITY;
    float PARTICLE_FORCE_FRICTION;
    uint PARTICLE_DUMMY_0;
};


// referene : RenderOptions.py
const int BLEND = 0;
const int ADDITIVE = 1;
const int MULTIPLY = 2;
const int SUBTRACT = 3;

#define WORK_GROUP_SIZE 64

const int MAX_BONES_PER_VERTEX = 4;
const int MAX_BONES = 100;

const float PI = 3.14159265358979323846;
const float HALF_PI = PI * 0.5;
const float TWO_PI = PI * 2.0;
const float deg = PI / 180.0;

const vec3 kSphereCenter = vec3(1.0, 1.0, -2.0);
const float kSphereRadius = 1.0;
const vec3 kSphereAlbedo = vec3(0.8);
const vec3 kGroundAlbedo = vec3(0.0, 0.0, 0.04);
