#include "scene_constants.glsl"

uniform float N_SLOPE_VARIANCE;

uniform sampler2D spectrum_1_2_Sampler;
uniform sampler2D spectrum_3_4_Sampler;
uniform int FFT_SIZE;

uniform vec4 GRID_SIZES;
uniform float slopeVarianceDelta;

uniform float c;


#ifdef VERTEX_SHADER
layout(location = 0) in vec4 vertex;
out vec2 uv;
void main()
{
    uv = vertex.xy * 0.5 + 0.5;
    gl_Position = vertex;
}
#endif


#ifdef FRAGMENT_SHADER
in vec2 uv;
layout(location = 0) out vec4 color;

vec2 getSlopeVariances(vec2 k, float A, float B, float C, vec2 spectrumSample)
{
    float w = 1.0 - exp(A * k.x * k.x + B * k.x * k.y + C * k.y * k.y);
    vec2 kw = k * w;
    return kw * kw * dot(spectrumSample, spectrumSample) * 2.0;
}

void main()
{
    const float SCALE = 10.0;
    float a = floor(uv.x * N_SLOPE_VARIANCE);
    float b = floor(uv.y * N_SLOPE_VARIANCE);
    float A = pow(a / (N_SLOPE_VARIANCE - 1.0), 4.0) * SCALE;
    float C = pow(c / (N_SLOPE_VARIANCE - 1.0), 4.0) * SCALE;
    float B = (2.0 * b / (N_SLOPE_VARIANCE - 1.0) - 1.0) * sqrt(A * C);
    A = -0.5 * A;
    B = - B;
    C = -0.5 * C;

    vec2 slopeVariances = vec2(slopeVarianceDelta);
    vec4 spectrum12;
    vec4 spectrum34;

    for (int y = 0; y < FFT_SIZE; ++y)
    {
        for (int x = 0; x < FFT_SIZE; ++x)
        {
            int i = x >= (FFT_SIZE / 2) ? x - FFT_SIZE : x;
            int j = y >= (FFT_SIZE / 2) ? y - FFT_SIZE : y;
            vec2 k = 2.0 * PI * vec2(i, j);

            spectrum12 = texture2D(spectrum_1_2_Sampler, vec2(float(x) + 0.5, float(y) + 0.5) / float(FFT_SIZE));
            spectrum34 = texture2D(spectrum_3_4_Sampler, vec2(float(x) + 0.5, float(y) + 0.5) / float(FFT_SIZE));

            slopeVariances += getSlopeVariances(k / GRID_SIZES.x, A, B, C, spectrum12.xy) * 100.0;
            slopeVariances += getSlopeVariances(k / GRID_SIZES.y, A, B, C, spectrum12.zw) * 100.0;
            slopeVariances += getSlopeVariances(k / GRID_SIZES.z, A, B, C, spectrum34.xy) * 100.0;
            slopeVariances += getSlopeVariances(k / GRID_SIZES.w, A, B, C, spectrum34.zw) * 100.0;
        }
    }
    color = slopeVariances.xxxy;
}
#endif