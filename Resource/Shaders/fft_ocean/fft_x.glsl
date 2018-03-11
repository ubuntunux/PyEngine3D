#ifdef GL_VERTEX_SHADER
varying vec2 uvIn;

void main() {
    uvIn = gl_Vertex.zw;
    gl_Position = vec4(gl_Vertex.xy, 0.0, 1.0);
}
#endif


#ifdef GL_FRAGMENT_SHADER
#extension GL_EXT_gpu_shader4 : enable

uniform sampler2D butterflySampler;
uniform sampler2DArray imgSampler; // 2 complex inputs (= 4 values) per layer

uniform float pass;

varying vec2 uv;

// performs two FFTs on two inputs packed in a single texture
// returns two results packed in a single vec4
vec4 fft2(int layer, vec2 i, vec2 w) {
    vec4 input1 = texture2DArrayLod(imgSampler, vec3(i.x, uv.y, layer), 0.0);
    vec4 input2 = texture2DArrayLod(imgSampler, vec3(i.y, uv.y, layer), 0.0);
    float res1x = w.x * input2.x - w.y * input2.y;
    float res1y = w.y * input2.x + w.x * input2.y;
    float res2x = w.x * input2.z - w.y * input2.w;
    float res2y = w.y * input2.z + w.x * input2.w;
    return input1 + vec4(res1x, res1y, res2x, res2y);
}

void main() {
    vec4 data = texture2DLod(butterflySampler, vec2(uv.x, pass), 0.0);
    vec2 i = data.xy;
    vec2 w = data.zw;

    gl_FragColor = fft2(gl_PrimitiveID, i, w);
}
#endif