in vec3 position;

uniform mat4 model;

void main() {
    gl_Position = perspective * view * model * vec4(position, 1.0f);
}