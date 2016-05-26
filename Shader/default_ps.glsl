uniform vec4 diffuseColor;
uniform vec3 camera_position;
uniform vec4 light_color;
uniform vec3 light_position;

varying vec3 worldPosition;
varying vec4 vertexColor;
varying vec3 normalVector;
varying vec3 cameraVector;
varying vec3 lightVector;

void main() {
    normalVector = normalize(normalVector);
    cameraVector = normalize(cameraVector);
    lightVector = normalize(lightVector);

    float intensity;
    vec4 color;
    vec3 n = normalize(normalVector);
    vec3 l = normalize(gl_LightSource[0].position).xyz;
    intensity = saturate(dot(l, n));
    color = gl_LightSource[0].ambient + gl_LightSource[0].diffuse * intensity + vertexColor;

    gl_FragColor = vertexColor;
    gl_FragColor.xyz = diffuseColor.xyz + n;
    gl_FragColor.xyz = abs(dot(cameraVector, n));
    vec3 specular = pow(saturate(dot(reflect(-lightVector, n), cameraVector)), 60.0f);
    gl_FragColor.xyz = saturate(dot(lightVector, n)) + specular;
    gl_FragColor.xyz *= light_color.xyz * light_color.w;
}