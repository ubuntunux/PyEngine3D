attribute vec3 position;
attribute vec4 color;
varying vec4 v_color;
varying vec3 normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 perspective;

void main() {
    v_color = color;
    normal = gl_NormalMatrix * gl_Normal;
    gl_Position = perspective * view * model * vec4(position, 1.0f);
}