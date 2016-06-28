// input
attribute vec3 position;
attribute vec4 color;
attribute vec3 normal;
attribute vec3 bitangent;
attribute vec3 tangent;
attribute vec2 texcoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 perspective;
uniform vec3 camera_position;
uniform vec3 light_position;

// output
varying vec3 worldPosition;
varying vec4 vertexColor;
varying vec3 normalVector;
varying mat3 tangentToWorld;
varying vec2 textureCoordinate;
varying vec3 cameraVector;
varying vec3 lightVector;

void main() {
    vertexColor = color;
    gl_Position = perspective * view * model * vec4(position, 1.0f);
    mat3 modelViewMatrix = view * model;
    worldPosition = modelViewMatrix * position;
    normalVector = modelViewMatrix * normal;
    tangentToWorld = transpose(mat3(modelViewMatrix * tangent, modelViewMatrix * bitangent, modelViewMatrix * normal));
    textureCoordinate = texcoord;

    cameraVector = camera_position - position;
    cameraVector = normalize(cameraVector);

    lightVector = light_position - position;
    lightVector = normalize(lightVector);
}