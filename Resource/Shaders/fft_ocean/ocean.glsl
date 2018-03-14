#extension GL_EXT_texture_array : enable

#include "scene_constants.glsl"
#include "utility.glsl"


uniform vec2 gridSize;
uniform vec4 GRID_SIZES;
uniform sampler2DArray fftWavesSampler;
uniform sampler3D slopeVarianceSampler;


#ifdef GL_VERTEX_SHADER
layout (location = 0) in vec3 vs_in_position;
layout (location = 1) in vec4 vs_in_color;
layout (location = 2) in vec3 vs_in_normal;
layout (location = 3) in vec3 vs_in_tangent;
layout (location = 4) in vec2 vs_in_tex_coord;
layout (location = 5) in vec2 offset;   // instance buffer

out vec2 u; // coordinates in world space used to compute P(u)
out vec3 P; // wave point P(u) in world space

vec2 oceanPos(vec4 vertex)
{
    vec3 cameraDir = normalize((INV_PROJECTION * vertex).xyz);
    vec3 worldDir = (INV_VIEW * vec4(cameraDir, 0.0)).xyz;
    float t = -CAMERA_POSITION.z / worldDir.z;
    return CAMERA_POSITION.xy + t * worldDir.xy;
}

void main()
{
    vec4 vertex_pos = vec4(vs_in_position, 1.0);
    u = oceanPos(vertex_pos);
    vec2 ux = oceanPos(vertex_pos + vec4(gridSize.x, 0.0, 0.0, 0.0));
    vec2 uy = oceanPos(vertex_pos + vec4(0.0, gridSize.y, 0.0, 0.0));
    vec2 dux = abs(ux - u) * 2.0;
    vec2 duy = abs(uy - u) * 2.0;

    vec3 dP = vec3(0.0);
    dP.z += texture2DArrayGrad(fftWavesSampler, vec3(u / GRID_SIZES.x, 0.0), dux / GRID_SIZES.x, duy / GRID_SIZES.x).x;
    dP.z += texture2DArrayGrad(fftWavesSampler, vec3(u / GRID_SIZES.y, 0.0), dux / GRID_SIZES.y, duy / GRID_SIZES.y).y;
    dP.z += texture2DArrayGrad(fftWavesSampler, vec3(u / GRID_SIZES.z, 0.0), dux / GRID_SIZES.z, duy / GRID_SIZES.z).z;
    dP.z += texture2DArrayGrad(fftWavesSampler, vec3(u / GRID_SIZES.w, 0.0), dux / GRID_SIZES.w, duy / GRID_SIZES.w).w;

    dP.xy += texture2DArrayGrad(fftWavesSampler, vec3(u / GRID_SIZES.x, 3.0), dux / GRID_SIZES.x, duy / GRID_SIZES.x).xy;
    dP.xy += texture2DArrayGrad(fftWavesSampler, vec3(u / GRID_SIZES.y, 3.0), dux / GRID_SIZES.y, duy / GRID_SIZES.y).zw;
    dP.xy += texture2DArrayGrad(fftWavesSampler, vec3(u / GRID_SIZES.z, 4.0), dux / GRID_SIZES.z, duy / GRID_SIZES.z).xy;
    dP.xy += texture2DArrayGrad(fftWavesSampler, vec3(u / GRID_SIZES.w, 4.0), dux / GRID_SIZES.w, duy / GRID_SIZES.w).zw;

    P = vec3(u + dP.xy, dP.z);

    gl_Position = VIEW_PROJECTION * vec4(P, 1.0);

    vec4 world_pos = INV_VIEW_ORIGIN * INV_PROJECTION * vec4(vs_in_position.xz + JITTER_OFFSET, -1.0, 1.0);
    world_pos.xyz /= world_pos.w;
    vec4 proj_pos = VIEW_PROJECTION * vec4(world_pos.xyz, 1.0);

    gl_Position = proj_pos;
}
#endif


#ifdef GL_FRAGMENT_SHADER
in vec2 u; // coordinates in world space used to compute P(u)
in vec3 P; // wave point P(u) in world space
layout (location = 0) out vec4 fs_output;

float meanFresnel(float cosThetaV, float sigmaV)
{
	return pow(1.0 - cosThetaV, 5.0 * exp(-2.69 * sigmaV)) / (1.0 + 22.7 * pow(sigmaV, 1.5));
}

float meanFresnel(vec3 V, vec3 N, vec2 sigmaSq)
{
    vec2 v = V.xy;
    vec2 t = v * v / (1.0 - V.z * V.z);
    float sigmaV2 = dot(t, sigmaSq);
    return meanFresnel(dot(V, N), sqrt(sigmaV2));
}


void main()
{
    vec3 V = normalize(CAMERA_POSITION.xyz - P);

    vec2 slopes = texture2DArray(fftWavesSampler, vec3(u / GRID_SIZES.x, 1.0)).xy;
    slopes += texture2DArray(fftWavesSampler, vec3(u / GRID_SIZES.y, 1.0)).zw;
    slopes += texture2DArray(fftWavesSampler, vec3(u / GRID_SIZES.z, 2.0)).xy;
    slopes += texture2DArray(fftWavesSampler, vec3(u / GRID_SIZES.w, 2.0)).zw;

    vec3 N = normalize(vec3(-slopes.x, -slopes.y, 1.0));
    if (dot(V, N) < 0.0)
    {
        N = reflect(N, V); // reflects backfacing normals
    }

    float Jxx = dFdx(u.x);
    float Jxy = dFdy(u.x);
    float Jyx = dFdx(u.y);
    float Jyy = dFdy(u.y);
    float A = Jxx * Jxx + Jyx * Jyx;
    float B = Jxx * Jxy + Jyx * Jyy;
    float C = Jxy * Jxy + Jyy * Jyy;
    const float SCALE = 10.0;
    float ua = pow(A / SCALE, 0.25);
    float ub = 0.5 + 0.5 * B / sqrt(A * C);
    float uc = pow(C / SCALE, 0.25);
    vec2 sigmaSq = texture(slopeVarianceSampler, vec3(ua, ub, uc)).xw;

    sigmaSq = max(sigmaSq, 2e-5);

    vec3 Ty = normalize(vec3(0.0, N.z, -N.y));
    vec3 Tx = cross(Ty, N);

    float fresnel = 0.02 + 0.98 * meanFresnel(V, N, sigmaSq);

    fs_output = vec4(1.0, 1.0, fresnel, 1.0);
}

#endif