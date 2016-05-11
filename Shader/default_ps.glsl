varying vec4 v_color;
varying vec3 normal;
uniform vec4 diffuseColor;

void main() {
    float intensity;
    vec4 color;
    vec3 n = normalize(normal);
    vec3 l = normalize(gl_LightSource[0].position).xyz;
    intensity = saturate(dot(l, n));
    color = gl_LightSource[0].ambient + gl_LightSource[0].diffuse * intensity + v_color;
    gl_FragColor = v_color;
    gl_FragColor.xyz = diffuseColor.xyz;
}