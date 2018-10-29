layout(std140, binding=0) uniform scene_constants
{
    float TIME;
    float JITTER_FRAME;
    bool RENDER_SSR;
    bool RENDER_SSAO;
    vec2 BACKBUFFER_SIZE;
    vec2 MOUSE_POS;
    vec3 SCENECONSTANTS_DUMMY_0;
    float DELTA_TIME;
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
    vec3 LIGHT_POSITION;
    float LIGHT_DUMMY_0;
    vec3 LIGHT_DIRECTION;
    float LIGHT_DUMMY_1;
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

layout(std140, binding=4) uniform point_light_constants
{
    POINT_LIGHT POINT_LIGHTS[MAX_POINT_LIGHTS];
};


layout(std140, binding=5) uniform particle_common
{
    vec3 PARTICLE_COLOR;
    bool PARTICLE_BILLBOARD;
    ivec2 PARTICLE_CELL_COUNT;
    int PARTICLE_BLEND_MODE;
    int PARTICLE_COMMON_DUMMY_0;
};

layout(std140, binding=6) uniform particle_infos
{
    mat4 PARTICLE_PARENT_MATRIX;
    mat4 PARTICLE_PARENT_INVERSE_MATRIX;
    vec2 PARTICLE_DELAY;
    vec2 PARTICLE_LIFE_TIME;
    vec3 PARTICLE_TRANSFORM_POSITION_MIN;
    float PARTICLE_FORCE_GRAVITY;
    vec3 PARTICLE_TRANSFORM_POSITION_MAX;
    float PARTICLE_FADE_IN;
    vec3 PARTICLE_TRANSFORM_ROTATION_MIN;
    float PARTICLE_FADE_OUT;
    vec3 PARTICLE_TRANSFORM_ROTATION_MAX;
    float PARTICLE_OPACITY;
    vec3 PARTICLE_TRANSFORM_SCALE_MIN;
    float PARTICLE_PLAY_SPEED;
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
    float PARTICLE_DUMMY_0;
    vec3 PARTICLE_VELOCITY_SCALE_MAX;
    float PARTICLE_DUMMY_1;
    mat4 PARTICLE_VECTOR_FIELD_MATRIX;
    mat4 PARTICLE_VECTOR_FIELD_INV_MATRIX;
};

// Storage Buffer Data
struct ParticleData
{
    mat4 parent_matrix;
    mat4 local_matrix;
    float delay;
    float life_time;
    float opacity;
    float elapsed_time;
    vec2 sequence_uv;
    vec2 next_sequence_uv;
    float sequence_ratio;
    int sequence_index;
    int next_sequence_index;
    int state;
    vec3 force;
    float dummy_0;
    vec3 transform_position;
    float dummy_1;
    vec3 transform_rotation;
    float dummy_2;
    vec3 transform_scale;
    float dummy_3;
    vec3 velocity_position;
    float dummy_4;
    vec3 velocity_rotation;
    float dummy_5;
    vec3 velocity_scale;
    float dummy_6;
};


struct DispatchIndirectCommand
{
    uint num_groups_x;
    uint num_groups_y;
    uint num_groups_z;
};


struct DrawElementsIndirectCommand
{
    uint vertex_count;
    uint instance_count;
    uint first_index;
    uint base_vertex;
    uint base_instance;
};


// referene : RenderOptions.py
const int BLEND = 0;
const int ADDITIVE = 1;
const int MULTIPLY = 2;
const int SUBTRACT = 3;

const int PARTICLE_STATE_NONE = 0;
const int PARTICLE_STATE_DELAY = 1;
const int PARTICLE_STATE_ALIVE = 2;
const int PARTICLE_STATE_DEAD = 3;

#define WORK_GROUP_SIZE 64

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
