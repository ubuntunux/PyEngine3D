#version 430 core

in struct DATA
{
    vec2 texcoord;
    vec3 position;
} data;

out vec4 result;

void main() {
    vec4 color = texture(texture_diffuse, data.texcoord.xy);
    result = vec4(color.xyz * color.xyz, 1.0);
}