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
    mat4 EMITTER_PARENT_MATRIX;
    vec3 EMITTER_COLOR;
    bool EMITTER_BILLBOARD;
    vec2 EMITTER_DELAY;
    vec2 EMITTER_LIFE_TIME;
    ivec2 EMITTER_CELL_COUNT;
    int EMITTER_LOOP;
    int EMITTER_BLEND_MODE;
    vec3 EMITTER_POSITION_MIN;
    float EMITTER_GRAVITY;
    vec3 EMITTER_POSITION_MAX;
    float EMITTER_OPACITY;
    vec3 EMITTER_VELOCITY_MIN;
    float EMITTER_PLAY_SPEED;
    vec3 EMITTER_VELOCITY_MAX;
    int EMITTER_TOTAL_CELL_COUNT;
    vec3 EMITTER_ROTATION_MIN;
    float EMITTER_FADE_IN;
    vec3 EMITTER_ROTATION_MAX;
    float EMITTER_FADE_OUT;
    vec3 EMITTER_ROTATION_VELOCITY_MIN;
    float EMITTER_DUMMY_0;
    vec3 EMITTER_ROTATION_VELOCITY_MAX;
    float EMITTER_DUMMY_1;
    vec3 EMITTER_SCALE_MIN;
    float EMITTER_DUMMY_2;
    vec3 EMITTER_SCALE_MAX;
    float EMITTER_DUMMY_3;
    vec3 EMITTER_SCALE_VELOCITY_MIN;
    float EMITTER_DUMMY_4;
    vec3 EMITTER_SCALE_VELOCITY_MAX;
    float EMITTER_DUMMY_5;
};


// Storage Buffer Data
struct EmitterData
{
    mat4 local_matrix;
    vec3 position;
    float delay;
    vec3 velocity;
    float life_time;
    vec3 rotation;
    int state;
    vec3 rotation_velocity;
    float opacity;
    vec3 scale;
    float elapsed_time;
    vec3 scale_velocity;
    float sequence_ratio;
    vec2 sequence_uv;
    vec2 next_sequence_uv;
    int sequence_index;
    int next_sequence_index;
    int loop_remain;
    float dummy_0;

};

// referene : RenderOptions.py
const int BLEND = 0;
const int ADDITIVE = 1;
const int MULTIPLY = 2;
const int SUBTRACT = 3;

const int EMITTER_STATE_NONE = 0;
const int EMITTER_STATE_DELAY = 1;
const int EMITTER_STATE_ALIVE = 2;
const int EMITTER_STATE_DEAD = 3;

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
