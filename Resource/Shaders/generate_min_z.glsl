uniform bool generate_min_z;

#ifdef COMPUTE_SHADER
layout(local_size_x = 1, local_size_y = 1) in;

layout(r32f, binding=0) uniform image2D img_input;
layout(r32f, binding=1) uniform image2D img_output;

void main()
{
    ivec2 imageRatio = imageSize(img_input) / imageSize(img_output);
    ivec2 pixel_coords = ivec2(gl_GlobalInvocationID.xy);
    ivec2 input_pixel_coords = pixel_coords * imageRatio;

    vec4 depth = imageLoad(img_input, input_pixel_coords);
    if(generate_min_z)
    {
        depth = min(depth, imageLoad(img_input, input_pixel_coords + ivec2(1, 0)));
        depth = min(depth, imageLoad(img_input, input_pixel_coords + ivec2(0, 1)));
        depth = min(depth, imageLoad(img_input, input_pixel_coords + ivec2(1, 1)));
    }
    else
    {
        depth = max(depth, imageLoad(img_input, input_pixel_coords + ivec2(1, 0)));
        depth = max(depth, imageLoad(img_input, input_pixel_coords + ivec2(0, 1)));
        depth = max(depth, imageLoad(img_input, input_pixel_coords + ivec2(1, 1)));
    }

    imageStore(img_output, pixel_coords, depth);
}
#endif