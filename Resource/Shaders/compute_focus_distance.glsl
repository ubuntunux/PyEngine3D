uniform float focus_sensitivity;

#ifdef COMPUTE_SHADER
layout(local_size_x = 1, local_size_y = 1) in;

layout(r32f, binding=0) uniform image2D img_input;
layout(r32f, binding=1) uniform image2D img_output;

void main()
{
    ivec2 pixel_coords = ivec2(gl_GlobalInvocationID.xy);
    ivec2 center_pos = imageSize(img_input) / 2;
    vec4 curr_depth = imageLoad(img_input, center_pos);
    vec4 prev_depth = imageLoad(img_output, pixel_coords);
    curr_depth = mix(prev_depth, curr_depth, focus_sensitivity);
    imageStore(img_output, pixel_coords, curr_depth);
}
#endif