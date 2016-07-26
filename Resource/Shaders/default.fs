uniform vec4 diffuseColor;
uniform vec3 camera_position;
uniform vec4 light_color;
uniform vec3 light_position;

uniform sampler2D textureDiffuse;
uniform sampler2D textureNormal;

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
    normalVector = normalize(normalVector);
    cameraVector = normalize(cameraVector);
    lightVector = normalize(lightVector);

    vec3 diffuse = texture(textureDiffuse, textureCoordinate.xy).xyz;
    vec3 normal = texture(textureNormal, textureCoordinate.xy).xyz;
    normal = normalize((tangentToWorld * vec4(normal * 2.0 - 1.0, 0.0)).xyz);

    vec3 diffuseLighting = diffuse * diffuseColor.xyz * saturate(dot(lightVector, normal));
    vec3 specularLighting = pow(saturate(dot(reflect(-lightVector, normal), cameraVector)), 60.0);
    gl_FragColor.xyz = diffuseLighting + specularLighting;
}