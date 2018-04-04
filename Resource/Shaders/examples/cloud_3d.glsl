#include "scene_constants.glsl"
#include "quad.glsl"

#ifdef GL_FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out float fs_output;

const int count = 500;
uniform vec4 spheres[count];
uniform float depth;
uniform float density;

void main() {
    vec3 uvw = vec3(vs_output.tex_coord, depth);
    float density_total = 0.0;
    for(int i=0; i<count; ++i)
    {
        vec3 diff = abs(spheres[i].xyz - uvw);
        diff = min(diff, abs(vec3(1.0) - diff));
        density_total += clamp(1.0 - length(diff) / spheres[i].w, 0.0, 1.0);
    }
    fs_output = density_total * density;
}
#endif