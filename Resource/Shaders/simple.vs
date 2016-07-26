// input
attribute vec3 position;

uniform mat4 model;
uniform mat4 view;
uniform mat4 perspective;

void main() {
    gl_Position = perspective * view * model * vec4(position, 1.0f);
}