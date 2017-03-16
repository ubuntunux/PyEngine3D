#version 430 core

in vec2 texcoord;

out vec4 result;

void main() {
    result = vec4(get_emissive_color(), get_opacity());
}