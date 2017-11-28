struct VERTEX_INPUT
{
    vec3 position;
    vec4 color;
    vec3 normal;
    vec3 tangent;
    vec2 tex_coord;
};

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
};

#ifdef VERTEX_SHADER
layout (location = 0) in VERTEX_INPUT vs_input;
layout (location = 0) out VERTEX_OUTPUT vs_output;

void main() {
    vs_output.tex_coord = vs_input.tex_coord;
    vs_output.position = vs_input.position;
    gl_Position = vec4(vs_input.position, 1.0);
}
#endif // VERTEX_SHADER