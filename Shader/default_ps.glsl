uniform vec4 diffuseColor;
uniform vec3 camera_position;

varying vec4 vertexColor;
varying vec3 normalVector;
varying vec3 cameraVector;

void main() {
    float intensity;
    vec4 color;
    vec3 n = normalize(normalVector);
    vec3 l = normalize(gl_LightSource[0].position).xyz;
    intensity = saturate(dot(l, n));
    color = gl_LightSource[0].ambient + gl_LightSource[0].diffuse * intensity + vertexColor;
    gl_FragColor = vertexColor;
    gl_FragColor.xyz = diffuseColor.xyz + normalVector;
}