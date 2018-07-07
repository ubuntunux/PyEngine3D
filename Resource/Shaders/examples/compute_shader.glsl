#extension GL_ARB_compute_shader : enable
#extension GL_ARB_shader_storage_buffer_object : enable;

#ifdef GL_COMPUTE_SHADER
layout( std140, binding=0 ) buffer Pos
{
    vec4 Positions[ ]; // array of structures
};

layout(local_size_x = 1, local_size_y = 1) in;

layout(binding=0, rgba16f) uniform image2D img_output;

void main()
{
  // base pixel colour for image
  vec4 pixel = vec4(1.0, 0.0, 0.0, 1.0);

  // get index in global work group i.e x,y position
  ivec2 pixel_coords = ivec2(gl_GlobalInvocationID.xy);

  // output to a specific pixel in the image
  imageStore(img_output, pixel_coords, pixel);
}
#endif