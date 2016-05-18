// input
attribute vec3 position;
attribute vec4 color;
attribute vec3 normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 perspective;
uniform vec3 camera_position;

// output
varying vec4 vertexColor;
varying vec3 normalVector;
varying vec3 cameraVector;

void main() {
    vertexColor = color;
    normalVector = normal; // gl_NormalMatrix * gl_Normal;
    gl_Position = perspective * view * model * vec4(position, 1.0f);
    cameraVector = camera_position - position;
    cameraVector = normalize(cameraVector);
}