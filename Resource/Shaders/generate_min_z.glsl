#ifdef COMPUTE_SHADER
layout(local_size_x = 1, local_size_y = 1) in;

layout(r32f, binding=0) uniform image2D img_input;
layout(r32f, binding=1) uniform image2D img_output;

void main()
{
    ivec2 imageRatio = imageSize(img_input) / imageSize(img_output);
    ivec2 pixel_coords = ivec2(gl_GlobalInvocationID.xy);
    ivec2 input_pixel_coords = pixel_coords * imageRatio;

    vec4 min_depth = imageLoad(img_input, input_pixel_coords);
    min_depth = min(min_depth, imageLoad(img_input, input_pixel_coords + ivec2(1, 0)));
    min_depth = min(min_depth, imageLoad(img_input, input_pixel_coords + ivec2(0, 1)));
    min_depth = min(min_depth, imageLoad(img_input, input_pixel_coords + ivec2(1, 1)));

    imageStore(img_output, pixel_coords, min_depth);
}
#endif