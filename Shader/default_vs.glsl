attribute vec4 position;
attribute vec4 color;
varying vec4 v_color;
varying vec3 normal;
void main() {
    v_color = color;
    normal = gl_NormalMatrix * gl_Normal;
    gl_Position = gl_ModelViewProjectionMatrix * position * 0.2f;
}