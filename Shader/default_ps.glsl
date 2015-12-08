varying vec3 normal;
void main() {
    float intensity;
    vec4 color;
    vec3 n = normalize(normal);
    vec3 l = normalize(gl_LightSource[0].position).xyz;        
    intensity = saturate(dot(l, n));
    color = gl_LightSource[0].ambient + gl_LightSource[0].diffuse * intensity;
    gl_FragColor = color;
}