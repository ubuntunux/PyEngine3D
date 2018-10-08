//#extension GL_ARB_compute_shader : enable;
//#extension GL_ARB_shader_storage_buffer_object : enable;

#ifdef COMPUTE_SHADER
layout(local_size_x = 1, local_size_y = 1) in;

layout(rgba16f, binding=0) uniform image2D img_output;

layout(std430, binding=1) buffer InputPos { vec4 color; };
layout(std430, binding=2) buffer InputPos2 { vec4 color2; };

void main()
{
  // base pixel colour for image
  vec4 pixel = vec4(1.0, 0.0, 0.0, 1.0);

  // get index in global work group i.e x,y position
  ivec2 pixel_coords = ivec2(gl_GlobalInvocationID.xy);

  pixel.xy = vec2(pixel_coords.x, pixel_coords.y) / vec2(imageSize(img_output));

  pixel = color + color2;

  // output to a specific pixel in the image
  imageStore(img_output, pixel_coords, pixel);
}
#endif