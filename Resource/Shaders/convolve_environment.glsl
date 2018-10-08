#include "scene_constants.glsl"
#include "quad.glsl"

uniform samplerCube texture_environment;
uniform mat4 face_matrix;
uniform float lod;
uniform float mipmap_count;

#ifdef FRAGMENT_SHADER
layout (location = 0) in VERTEX_OUTPUT vs_output;
layout (location = 0) out vec4 fs_output;

void main()
{
    vec3 normal;
    normal.x = vs_output.tex_coord.x * 2.0 - 1.0;
    normal.y = 1.0 - vs_output.tex_coord.y * 2.0;
    normal.z = 1.0;
    normal = normalize(normal);
    normal = (vec4(normal, 0.0) * face_matrix).xyz;

    vec3 up = vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(up, normal));
    up = cross(normal, right);

    vec3 sampledColour = vec3(0,0,0);
    float total_weight = 0.0;

    const float dphi = PI / 180.0;
    const float dtheta = HALF_PI / 90.0;
    const float rad_range = HALF_PI * clamp(lod / mipmap_count, 0.0, 1.0);

    for(float phi = 0.0; phi <= PI; phi += dphi)
    {
        for(float theta = 0.0; theta <= rad_range; theta += dtheta)
        {
            float c_phi, s_phi, c_theta, s_theta;
            c_phi = cos(phi);
            s_phi = sin(phi);
            c_theta = cos(theta);
            s_theta = sin(theta);

            vec3 temp = right * c_phi + up * s_phi;
            vec3 sampleVector = normal * c_theta + temp * s_theta;

            sampledColour += textureCube( texture_environment, sampleVector ).rgb * c_theta;
            total_weight += c_theta;
        }
    }

    fs_output = vec4(sampledColour / total_weight, 1.0);
    // fs_output = vec4(PI * sampledColour / index, 1.0);
}
#endif // FRAGMENT_SHADER