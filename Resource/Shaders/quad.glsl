#version 430 core

//----------- INPUT and OUTPUT ---------------//

struct VERTEX_INPUT
{
    layout(location=0) vec3 position;
    layout(location=1) vec4 color;
    layout(location=2) vec3 normal;
    layout(location=3) vec3 tangent;
    layout(location=4) vec2 tex_coord;
};

struct VERTEX_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
};

//----------- VERTEX_SHADER ---------------//

#ifdef VERTEX_SHADER
in VERTEX_INPUT vs_input;
out VERTEX_OUTPUT vs_output;

void main() {
    vs_output.tex_coord = vs_input.tex_coord;
    vs_output.position = vs_input.position;
    gl_Position = vec4(vs_input.position, 1.0);
}
#endif // VERTEX_SHADER