#include "quad.glsl"

struct GEOMETRY_OUTPUT
{
    vec2 tex_coord;
    vec3 position;
    vec3 color;
};


#ifdef GEOMETRY_SHADER
layout (invocations = 5, triangles) in;
layout (triangle_strip, max_vertices = 3) out;
layout (location = 0) in VERTEX_OUTPUT gs_input[];
layout (location = 0) out GEOMETRY_OUTPUT gs_output;

void main()
{
    gl_Layer = gl_InvocationID;
    for(int i = 0; i < gl_in.length(); ++i)
    {
        gs_output.position = gs_input[i].position;
        gs_output.tex_coord = gs_input[i].tex_coord;
        gl_Position = gl_in[i].gl_Position;
        gl_Position.xy *= 0.1;
        gl_Position.xy += vec2(0.1 * float(gl_Layer));


        if(0 == gl_Layer)
        {
            gs_output.color = vec3(1.0, 1.0, 1.0);
        }
        else if(1 == gl_Layer)
        {
            gs_output.color = vec3(0.0, 1.0, 0.0);
        }
        else if(2 == gl_Layer)
        {
            gs_output.color = vec3(0.0, 0.0, 0.0);
        }
        else if(3 == gl_Layer)
        {
            gs_output.color = vec3(1.0, 1.0, 1.0);
        }
        else
        {
            gs_output.color = vec3(0.0, 0.0, 1.0);
        }

        EmitVertex();
    }
    EndPrimitive();
}
#endif

#ifdef FRAGMENT_SHADER
layout (location = 0) in GEOMETRY_OUTPUT gs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    fs_output.xyz = gs_output.color;
    fs_output.w = 1.0;
}
#endif