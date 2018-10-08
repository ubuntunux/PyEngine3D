#ifdef VERTEX_SHADER
void main() {
    gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
}
#endif


#ifdef FRAGMENT_SHADER
layout(location = 0) out vec4 fs_output;
void main() {
    fs_output = vec4(0.0, 0.0, 0.0, 1.0);
}
#endif