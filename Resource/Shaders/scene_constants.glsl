layout(std140, binding=0) uniform sceneConstants
{
    float TIME;
    float RENDER_SSR;
    float RENDER_SSAO;
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

const int MAX_BONES_PER_VERTEX = 4;
const int MAX_BONES = 100;
const float SHADOW_BIAS = -0.0001;