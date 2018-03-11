#ifdef _VERTEX_

varying vec2 uvIn;

void main() {
    uvIn = gl_Vertex.zw;
    gl_Position = vec4(gl_Vertex.xy, 0.0, 1.0);
}

#endif

#ifdef _GEOMETRY_
#version 120
#extension GL_EXT_gpu_shader4 : enable
#extension GL_EXT_geometry_shader4 : enable

uniform int nLayers;

varying in vec2 uvIn[];
varying vec2 uv;

void main() {
    for (int i = 0; i < 5; ++i) {
        gl_Layer = i;
        gl_PrimitiveID = i;
        gl_Position = gl_PositionIn[0];
        uv = uvIn[0];
        EmitVertex();
        gl_Position = gl_PositionIn[1];
        uv = uvIn[1];
        EmitVertex();
        gl_Position = gl_PositionIn[2];
        uv = uvIn[2];
        EmitVertex();
        EndPrimitive();
    }
}

#endif

#ifdef _FRAGMENT_
#extension GL_EXT_gpu_shader4 : enable

uniform sampler2D butterflySampler;
uniform sampler2DArray imgSampler; // 2 complex inputs (= 4 values) per layer

uniform float pass;

varying vec2 uv;

// performs two FFTs on two inputs packed in a single texture
// returns two results packed in a single vec4
vec4 fft2(int layer, vec2 i, vec2 w) {
    vec4 input1 = texture2DArrayLod(imgSampler, vec3(uv.x, i.x, layer), 0.0);
    vec4 input2 = texture2DArrayLod(imgSampler, vec3(uv.x, i.y, layer), 0.0);
    float res1x = w.x * input2.x - w.y * input2.y;
    float res1y = w.y * input2.x + w.x * input2.y;
    float res2x = w.x * input2.z - w.y * input2.w;
    float res2y = w.y * input2.z + w.x * input2.w;
    return input1 + vec4(res1x, res1y, res2x, res2y);
}

void main() {
    vec4 data = texture2DLod(butterflySampler, vec2(uv.y, pass), 0.0);
    vec2 i = data.xy;
    vec2 w = data.zw;

    gl_FragColor = fft2(gl_PrimitiveID, i, w);
}

#endif