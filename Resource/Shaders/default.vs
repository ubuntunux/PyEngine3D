// input
attribute vec3 position;
attribute vec4 color;
attribute vec3 normal;
attribute vec3 tangent;
attribute vec2 texcoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 perspective;
uniform mat4 mvp;
uniform vec3 camera_position;
uniform vec3 light_position;

// output
varying vec3 worldPosition;
varying vec4 vertexColor;
varying vec3 normalVector;
varying mat4 tangentToWorld;
varying vec2 textureCoordinate;
varying vec3 cameraVector;
varying vec3 cameraPosition;
varying vec3 lightVector;
varying vec3 lightPosition;

void main() {
    vertexColor = color;
    gl_Position = mvp * vec4(position, 1.0f);
    worldPosition = model * vec4(position, 1.0);
    normalVector = model * vec4(normal, 0.0);
    vec3 bitangent = cross(tangent, normal);
    tangentToWorld = mat4(model * vec4(tangent, 0.0), model * vec4(bitangent,0.0), model * vec4(normal, 0.0), model * vec4(0.0, 0.0, 0.0, 1.0));
    textureCoordinate = texcoord;

    cameraPosition = camera_position;
    cameraVector = camera_position - worldPosition;
    cameraVector = normalize(cameraVector);

    lightPosition = light_position;
    lightVector = light_position - worldPosition;
    lightVector = normalize(lightVector);
}