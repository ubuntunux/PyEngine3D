uniform sampler2D butterflySampler;
uniform sampler2DArray imgSampler; // 2 complex inputs (= 4 values) per layer
uniform float pass;

// performs two FFTs on two inputs packed in a single texture
// returns two results packed in a single vec4
vec4 fft2(int layer, vec2 i, vec2 w, vec2 uv)
{
    vec4 input1 = texture2DArray(imgSampler, vec3(uv.x, i.x, layer), 0.0);
    vec4 input2 = texture2DArray(imgSampler, vec3(uv.x, i.y, layer), 0.0);
    float res1x = w.x * input2.x - w.y * input2.y;
    float res1y = w.y * input2.x + w.x * input2.y;
    float res2x = w.x * input2.z - w.y * input2.w;
    float res2y = w.y * input2.z + w.x * input2.w;
    return input1 + vec4(res1x, res1y, res2x, res2y);
}


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
layout(location = 0) out vec4 color0;
layout(location = 1) out vec4 color1;
layout(location = 2) out vec4 color2;
layout(location = 3) out vec4 color3;
layout(location = 4) out vec4 color4;

void main()
{
    vec4 data = texture2D(butterflySampler, vec2(uv.y, pass), 0.0);
    vec2 i = data.xy;
    vec2 w = data.zw;

    color0 = fft2(0, i, w, uv);
    color1 = fft2(1, i, w, uv);
    color2 = fft2(2, i, w, uv);
    color3 = fft2(3, i, w, uv);
    color4 = fft2(4, i, w, uv);
}
#endif