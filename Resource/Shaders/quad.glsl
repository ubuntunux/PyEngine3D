struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
};

#ifdef VERTEX_SHADER
layout (location = 0) in vec4 vs_in_position;
layout (location = 0) out VERTEX_OUTPUT vs_output;

void main() {
    vs_output.position = vs_in_position.xyz;
    vs_output.tex_coord = vs_in_position.xy * 0.5 + 0.5;
    gl_Position = vs_in_position;
    gl_Position.z = -1.0;
    gl_Position.w = 1.0;
}
#endif // VERTEX_SHADER