#version 430 core

in struct VERTEX_OUTPUT
{
    vec2 texcoord;
    vec3 position;
} vs_output;

out vec4 result;

void main() {
    vec4 color = texture(texture_diffuse, vs_output.texcoord.xy);
    result = color;
}